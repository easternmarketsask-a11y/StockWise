/**
 * Firebase Cloud Functions - Main Entry Point
 * StockWise Points Management System
 * 
 * Functions:
 * 1. cloverWebhook - 接收 Clover POS webhook 并自动发放积分
 * 2. csvImport - 批量导入历史交易并发放积分
 * 3. validateCSV - 验证 CSV 格式（不实际导入）
 */

const functions = require('firebase-functions');
const admin = require('firebase-admin');
const {handleCloverWebhook} = require('./cloverWebhook');
const {handleCSVImport, validateCSV} = require('./csvImport');

// 初始化 Firebase Admin SDK
admin.initializeApp();

/**
 * Clover Webhook 接收器
 * 
 * URL: https://us-central1-{project-id}.cloudfunctions.net/cloverWebhook
 * Method: POST
 * Headers: x-clover-signature (必需)
 * 
 * 处理流程：
 * 1. 验证 Clover 签名
 * 2. 只处理 PAYMENT_PROCESSED 事件
 * 3. 提取手机号和消费金额
 * 4. 查询会员并计算积分（含倍率）
 * 5. 原子更新 Firestore（积分 + 等级）
 * 6. 返回 200 状态码
 */
exports.cloverWebhook = functions
  .region('us-central1')
  .runWith({
    timeoutSeconds: 60,
    memory: '256MB',
  })
  .https.onRequest(async (req, res) => {
    // 只接受 POST 请求
    if (req.method !== 'POST') {
      return res.status(405).json({
        success: false,
        error: 'Method not allowed',
      });
    }

    // 从环境变量获取 Clover App Secret
    const cloverAppSecret = functions.config().clover?.app_secret;
    if (!cloverAppSecret) {
      console.error('CLOVER_APP_SECRET not configured');
      return res.status(500).json({
        success: false,
        error: 'Server configuration error',
      });
    }

    // 处理 webhook
    await handleCloverWebhook(req, res, cloverAppSecret);
  });

/**
 * CSV 批量导入积分
 * 
 * URL: https://us-central1-{project-id}.cloudfunctions.net/csvImport
 * Method: POST
 * Body: {
 *   csvContent: "date,amount,phone,order_id\n2026-03-01,45.50,+16131234567,ORDER123",
 *   adminUid: "admin_user_id"
 * }
 * 
 * CSV 格式：
 * - date: 交易日期（YYYY-MM-DD）
 * - amount: 消费金额（CAD）
 * - phone: 手机号（+1XXXXXXXXXX）
 * - order_id: 订单 ID（可选）
 * 
 * 返回：
 * {
 *   success: true,
 *   results: {
 *     total: 100,
 *     success: 95,
 *     failed: 5,
 *     successRate: "95.00%",
 *     errors: [...],
 *     details: [...]
 *   }
 * }
 */
exports.csvImport = functions
  .region('us-central1')
  .runWith({
    timeoutSeconds: 540, // 9 分钟（最大值）
    memory: '512MB',
  })
  .https.onRequest(async (req, res) => {
    // 只接受 POST 请求
    if (req.method !== 'POST') {
      return res.status(405).json({
        success: false,
        error: 'Method not allowed',
      });
    }

    // 验证管理员权限
    const {adminUid} = req.body;
    if (!adminUid) {
      return res.status(401).json({
        success: false,
        error: 'Unauthorized: adminUid required',
      });
    }

    try {
      // 检查管理员权限
      const adminDoc = await admin.firestore()
        .collection('members')
        .doc(adminUid)
        .get();

      if (!adminDoc.exists || adminDoc.data().role !== 'admin') {
        return res.status(403).json({
          success: false,
          error: 'Forbidden: Admin role required',
        });
      }

      // 处理 CSV 导入
      await handleCSVImport(req, res);
    } catch (error) {
      console.error('Error in csvImport:', error);
      return res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  });

/**
 * 验证 CSV 格式（不实际导入）
 * 
 * URL: https://us-central1-{project-id}.cloudfunctions.net/validateCSV
 * Method: POST
 * Body: {
 *   csvContent: "date,amount,phone,order_id\n..."
 * }
 * 
 * 返回：
 * {
 *   success: true,
 *   data: {
 *     totalRows: 100,
 *     sample: [...], // 前 5 条数据
 *     columns: ["date", "amount", "phone", "order_id"]
 *   }
 * }
 */
exports.validateCSV = functions
  .region('us-central1')
  .runWith({
    timeoutSeconds: 60,
    memory: '256MB',
  })
  .https.onRequest(async (req, res) => {
    // 只接受 POST 请求
    if (req.method !== 'POST') {
      return res.status(405).json({
        success: false,
        error: 'Method not allowed',
      });
    }

    await validateCSV(req, res);
  });

/**
 * 手动添加积分（管理员功能）
 * 
 * URL: https://us-central1-{project-id}.cloudfunctions.net/manualAddPoints
 * Method: POST
 * Body: {
 *   adminUid: "admin_user_id",
 *   memberId: "member_user_id",
 *   points: 100,
 *   reason: "手动调整"
 * }
 */
exports.manualAddPoints = functions
  .region('us-central1')
  .runWith({
    timeoutSeconds: 60,
    memory: '256MB',
  })
  .https.onRequest(async (req, res) => {
    if (req.method !== 'POST') {
      return res.status(405).json({
        success: false,
        error: 'Method not allowed',
      });
    }

    try {
      const {adminUid, memberId, points, reason} = req.body;

      // 验证必需字段
      if (!adminUid || !memberId || !points) {
        return res.status(400).json({
          success: false,
          error: 'Missing required fields: adminUid, memberId, points',
        });
      }

      // 验证管理员权限
      const adminDoc = await admin.firestore()
        .collection('members')
        .doc(adminUid)
        .get();

      if (!adminDoc.exists || adminDoc.data().role !== 'admin') {
        return res.status(403).json({
          success: false,
          error: 'Forbidden: Admin role required',
        });
      }

      // 导入 addPoints 函数
      const {addPoints} = require('./pointsService');

      // 添加积分
      const result = await addPoints(
        memberId,
        points,
        `MANUAL_${Date.now()}`,
        0,
        'manual_admin',
        reason || `管理员手动添加 ${points} 积分`
      );

      return res.status(200).json({
        success: true,
        message: 'Points added successfully',
        data: result,
      });
    } catch (error) {
      console.error('Error in manualAddPoints:', error);
      return res.status(500).json({
        success: false,
        error: error.message,
      });
    }
  });
