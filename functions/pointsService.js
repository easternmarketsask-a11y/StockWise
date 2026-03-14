/**
 * Points Service - 积分计算和会员等级管理
 * 
 * 积分规则：
 * - 每 $1 CAD = 1 积分（基础）
 * - Bronze (0-999 分)：倍率 1.0x
 * - Silver (1000-4999 分)：倍率 1.5x
 * - Gold (5000+分)：倍率 2.0x
 */

const admin = require('firebase-admin');

/**
 * 会员等级定义
 */
const TIERS = {
  BRONZE: {
    name: 'bronze',
    minPoints: 0,
    maxPoints: 999,
    multiplier: 1.0,
  },
  SILVER: {
    name: 'silver',
    minPoints: 1000,
    maxPoints: 4999,
    multiplier: 1.5,
  },
  GOLD: {
    name: 'gold',
    minPoints: 5000,
    maxPoints: Infinity,
    multiplier: 2.0,
  },
};

/**
 * 根据累计积分确定会员等级
 * @param {number} lifetimePoints - 累计获得积分
 * @return {string} 会员等级 ('bronze' | 'silver' | 'gold')
 */
function getTierByPoints(lifetimePoints) {
  if (lifetimePoints >= TIERS.GOLD.minPoints) {
    return TIERS.GOLD.name;
  } else if (lifetimePoints >= TIERS.SILVER.minPoints) {
    return TIERS.SILVER.name;
  } else {
    return TIERS.BRONZE.name;
  }
}

/**
 * 获取等级倍率
 * @param {string} tier - 会员等级
 * @return {number} 积分倍率
 */
function getMultiplier(tier) {
  switch (tier) {
    case TIERS.GOLD.name:
      return TIERS.GOLD.multiplier;
    case TIERS.SILVER.name:
      return TIERS.SILVER.multiplier;
    case TIERS.BRONZE.name:
    default:
      return TIERS.BRONZE.multiplier;
  }
}

/**
 * 计算消费应得积分（含倍率）
 * @param {number} amount - 消费金额（CAD）
 * @param {string} currentTier - 当前会员等级
 * @return {number} 应得积分（向下取整）
 */
function calculatePoints(amount, currentTier) {
  const basePoints = amount; // 每 $1 = 1 积分
  const multiplier = getMultiplier(currentTier);
  return Math.floor(basePoints * multiplier);
}

/**
 * 根据手机号查询会员
 * @param {string} phone - 手机号（格式：+1XXXXXXXXXX）
 * @return {Promise<Object|null>} 会员数据或 null
 */
async function getMemberByPhone(phone) {
  const db = admin.firestore();
  
  // 标准化手机号格式
  let normalizedPhone = phone.trim();
  if (!normalizedPhone.startsWith('+1')) {
    normalizedPhone = '+1' + normalizedPhone.replace(/\D/g, '');
  }

  try {
    const snapshot = await db.collection('members')
      .where('phone', '==', normalizedPhone)
      .limit(1)
      .get();

    if (snapshot.empty) {
      return null;
    }

    const doc = snapshot.docs[0];
    return {
      id: doc.id,
      ...doc.data(),
    };
  } catch (error) {
    console.error('Error fetching member by phone:', error);
    throw error;
  }
}

/**
 * 添加积分并更新会员等级（原子操作）
 * @param {string} memberId - 会员 ID
 * @param {number} points - 要添加的积分
 * @param {string} orderId - 订单 ID
 * @param {number} amount - 消费金额
 * @param {string} source - 来源（默认 'clover'）
 * @param {string} description - 交易描述
 * @return {Promise<Object>} 更新结果
 */
async function addPoints(memberId, points, orderId, amount, source = 'clover', description = '') {
  const db = admin.firestore();
  const batch = db.batch();

  try {
    // 获取当前会员数据
    const memberRef = db.collection('members').doc(memberId);
    const memberDoc = await memberRef.get();

    if (!memberDoc.exists) {
      throw new Error(`Member ${memberId} not found`);
    }

    const memberData = memberDoc.data();
    const currentTotalPoints = memberData.totalPoints || 0;
    const currentLifetimePoints = memberData.lifetimePoints || 0;

    // 计算新的积分
    const newTotalPoints = currentTotalPoints + points;
    const newLifetimePoints = currentLifetimePoints + points;

    // 检查是否需要升级等级
    const newTier = getTierByPoints(newLifetimePoints);
    const oldTier = memberData.tier || 'bronze';

    // 更新会员数据
    batch.update(memberRef, {
      totalPoints: newTotalPoints,
      lifetimePoints: newLifetimePoints,
      tier: newTier,
      updatedAt: admin.firestore.FieldValue.serverTimestamp(),
    });

    // 创建积分交易记录
    const transactionRef = db.collection('points_transactions').doc();
    batch.set(transactionRef, {
      memberId: memberId,
      type: 'earn',
      points: points,
      orderId: orderId,
      amount: amount,
      description: description || `消费 $${amount.toFixed(2)} 获得 ${points} 积分`,
      source: source,
      createdAt: admin.firestore.FieldValue.serverTimestamp(),
    });

    // 提交批量写入
    await batch.commit();

    return {
      success: true,
      memberId: memberId,
      pointsAdded: points,
      newTotalPoints: newTotalPoints,
      newLifetimePoints: newLifetimePoints,
      oldTier: oldTier,
      newTier: newTier,
      tierUpgraded: newTier !== oldTier,
    };
  } catch (error) {
    console.error('Error adding points:', error);
    throw error;
  }
}

/**
 * 批量处理积分（用于 CSV 导入）
 * @param {Array<Object>} transactions - 交易数组 [{date, amount, phone, order_id}]
 * @return {Promise<Object>} 处理结果统计
 */
async function batchProcessPoints(transactions) {
  const results = {
    total: transactions.length,
    success: 0,
    failed: 0,
    errors: [],
    details: [],
  };

  for (const tx of transactions) {
    try {
      const {date, amount, phone, order_id} = tx;

      // 查询会员
      const member = await getMemberByPhone(phone);
      if (!member) {
        results.failed++;
        results.errors.push({
          phone: phone,
          error: 'Member not found',
        });
        continue;
      }

      // 计算积分
      const points = calculatePoints(amount, member.tier);

      // 添加积分
      const result = await addPoints(
        member.id,
        points,
        order_id,
        amount,
        'csv_import',
        `CSV 导入：${date} 消费 $${amount.toFixed(2)}`
      );

      results.success++;
      results.details.push({
        phone: phone,
        memberId: member.id,
        amount: amount,
        points: points,
        tierUpgraded: result.tierUpgraded,
      });
    } catch (error) {
      results.failed++;
      results.errors.push({
        phone: tx.phone,
        error: error.message,
      });
      console.error(`Error processing transaction for ${tx.phone}:`, error);
    }
  }

  return results;
}

module.exports = {
  TIERS,
  getTierByPoints,
  getMultiplier,
  calculatePoints,
  getMemberByPhone,
  addPoints,
  batchProcessPoints,
};
