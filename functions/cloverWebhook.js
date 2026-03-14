/**
 * Clover Webhook Handler - 处理 Clover POS 支付事件
 * 
 * 功能：
 * 1. 验证 Clover 签名（x-clover-signature header）
 * 2. 只处理 PAYMENT_PROCESSED 事件
 * 3. 提取顾客手机号和消费金额
 * 4. 查询会员并发放积分
 * 5. 原子更新 Firestore
 */

const crypto = require('crypto');
const {
  getMemberByPhone,
  calculatePoints,
  addPoints,
} = require('./pointsService');

/**
 * 验证 Clover Webhook 签名
 * @param {string} payload - 请求体（原始字符串）
 * @param {string} signature - x-clover-signature header
 * @param {string} secret - Clover App Secret
 * @return {boolean} 签名是否有效
 */
function verifyCloverSignature(payload, signature, secret) {
  if (!signature || !secret) {
    return false;
  }

  try {
    const hmac = crypto.createHmac('sha256', secret);
    hmac.update(payload);
    const computedSignature = hmac.digest('base64');
    
    return crypto.timingSafeEqual(
      Buffer.from(signature),
      Buffer.from(computedSignature)
    );
  } catch (error) {
    console.error('Error verifying signature:', error);
    return false;
  }
}

/**
 * 从 Clover 支付事件中提取手机号
 * @param {Object} payment - Clover payment 对象
 * @return {string|null} 手机号或 null
 */
function extractPhoneNumber(payment) {
  // Clover 可能在不同位置存储手机号
  // 优先级：customer.phoneNumbers -> tender.tipAmount -> cardTransaction.extra
  
  try {
    // 方法 1: 从 customer 对象获取
    if (payment.customer && payment.customer.phoneNumbers) {
      const phoneNumbers = payment.customer.phoneNumbers;
      if (phoneNumbers.length > 0) {
        return phoneNumbers[0].phoneNumber;
      }
    }

    // 方法 2: 从 order 对象获取
    if (payment.order && payment.order.customer && payment.order.customer.phoneNumbers) {
      const phoneNumbers = payment.order.customer.phoneNumbers;
      if (phoneNumbers.length > 0) {
        return phoneNumbers[0].phoneNumber;
      }
    }

    // 方法 3: 从 metadata 或 note 获取
    if (payment.note) {
      const phoneMatch = payment.note.match(/\+?1?\d{10}/);
      if (phoneMatch) {
        return phoneMatch[0];
      }
    }

    return null;
  } catch (error) {
    console.error('Error extracting phone number:', error);
    return null;
  }
}

/**
 * 从 Clover 支付事件中提取消费金额
 * @param {Object} payment - Clover payment 对象
 * @return {number} 消费金额（CAD，已转换为元）
 */
function extractAmount(payment) {
  try {
    // Clover 金额以分为单位
    const amountInCents = payment.amount || 0;
    return amountInCents / 100;
  } catch (error) {
    console.error('Error extracting amount:', error);
    return 0;
  }
}

/**
 * 处理 Clover Webhook 事件
 * @param {Object} req - Express request 对象
 * @param {Object} res - Express response 对象
 * @param {string} cloverAppSecret - Clover App Secret（用于验证签名）
 * @return {Promise<void>}
 */
async function handleCloverWebhook(req, res, cloverAppSecret) {
  try {
    // 1. 验证签名
    const signature = req.headers['x-clover-signature'];
    const rawBody = JSON.stringify(req.body);
    
    if (!verifyCloverSignature(rawBody, signature, cloverAppSecret)) {
      console.warn('Invalid Clover signature');
      return res.status(401).json({
        success: false,
        error: 'Invalid signature',
      });
    }

    // 2. 检查事件类型
    const eventType = req.body.type;
    if (eventType !== 'PAYMENT_PROCESSED') {
      console.log(`Ignoring event type: ${eventType}`);
      return res.status(200).json({
        success: true,
        message: 'Event type not processed',
      });
    }

    // 3. 提取支付数据
    const payment = req.body.payment || req.body.data || {};
    const orderId = payment.id || payment.order?.id || 'unknown';
    const phone = extractPhoneNumber(payment);
    const amount = extractAmount(payment);

    console.log(`Processing payment: orderId=${orderId}, phone=${phone}, amount=$${amount}`);

    // 4. 验证必需字段
    if (!phone) {
      console.warn('No phone number found in payment');
      return res.status(200).json({
        success: true,
        message: 'No phone number found, skipping points',
      });
    }

    if (amount <= 0) {
      console.warn('Invalid amount:', amount);
      return res.status(200).json({
        success: true,
        message: 'Invalid amount, skipping points',
      });
    }

    // 5. 查询会员
    const member = await getMemberByPhone(phone);
    if (!member) {
      console.log(`Member not found for phone: ${phone}`);
      return res.status(200).json({
        success: true,
        message: 'Member not found, skipping points',
      });
    }

    // 6. 计算积分
    const points = calculatePoints(amount, member.tier);
    console.log(`Calculated points: ${points} (tier: ${member.tier}, multiplier: ${member.tier === 'gold' ? '2.0x' : member.tier === 'silver' ? '1.5x' : '1.0x'})`);

    // 7. 添加积分（原子操作）
    const result = await addPoints(
      member.id,
      points,
      orderId,
      amount,
      'clover',
      `Clover 支付：订单 ${orderId}`
    );

    console.log('Points added successfully:', result);

    // 8. 返回成功响应
    return res.status(200).json({
      success: true,
      message: 'Points added successfully',
      data: {
        memberId: member.id,
        memberName: member.name,
        phone: phone,
        amount: amount,
        pointsAdded: points,
        newTotalPoints: result.newTotalPoints,
        tier: result.newTier,
        tierUpgraded: result.tierUpgraded,
      },
    });
  } catch (error) {
    console.error('Error processing Clover webhook:', error);
    
    // 返回 200 避免 Clover 重试
    return res.status(200).json({
      success: false,
      error: error.message,
      message: 'Error processed, will not retry',
    });
  }
}

module.exports = {
  verifyCloverSignature,
  extractPhoneNumber,
  extractAmount,
  handleCloverWebhook,
};
