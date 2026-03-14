/**
 * CSV Batch Import - 批量导入历史交易并发放积分
 * 
 * CSV 格式：date, amount, phone, order_id
 * 示例：2026-03-01,45.50,+16131234567,ORDER123
 */

const {parse} = require('csv-parse/sync');
const {batchProcessPoints} = require('./pointsService');

/**
 * 解析 CSV 内容
 * @param {string} csvContent - CSV 文件内容
 * @return {Array<Object>} 解析后的交易数组
 */
function parseCSV(csvContent) {
  try {
    const records = parse(csvContent, {
      columns: true,
      skip_empty_lines: true,
      trim: true,
    });

    // 验证和转换数据
    const transactions = records.map((record, index) => {
      const {date, amount, phone, order_id} = record;

      // 验证必需字段
      if (!date || !amount || !phone) {
        throw new Error(`Row ${index + 1}: Missing required fields (date, amount, phone)`);
      }

      // 转换金额为数字
      const parsedAmount = parseFloat(amount);
      if (isNaN(parsedAmount) || parsedAmount <= 0) {
        throw new Error(`Row ${index + 1}: Invalid amount: ${amount}`);
      }

      return {
        date: date.trim(),
        amount: parsedAmount,
        phone: phone.trim(),
        order_id: order_id ? order_id.trim() : `CSV_${date}_${phone}`,
      };
    });

    return transactions;
  } catch (error) {
    console.error('Error parsing CSV:', error);
    throw new Error(`CSV parsing failed: ${error.message}`);
  }
}

/**
 * 处理 CSV 批量导入请求
 * @param {Object} req - Express request 对象
 * @param {Object} res - Express response 对象
 * @return {Promise<void>}
 */
async function handleCSVImport(req, res) {
  try {
    // 1. 验证请求
    const {csvContent, adminUid} = req.body;

    if (!csvContent) {
      return res.status(400).json({
        success: false,
        error: 'Missing csvContent in request body',
      });
    }

    if (!adminUid) {
      return res.status(400).json({
        success: false,
        error: 'Missing adminUid in request body',
      });
    }

    console.log(`CSV import started by admin: ${adminUid}`);

    // 2. 解析 CSV
    const transactions = parseCSV(csvContent);
    console.log(`Parsed ${transactions.length} transactions from CSV`);

    if (transactions.length === 0) {
      return res.status(400).json({
        success: false,
        error: 'No valid transactions found in CSV',
      });
    }

    // 3. 批量处理积分
    const results = await batchProcessPoints(transactions);

    console.log('CSV import completed:', {
      total: results.total,
      success: results.success,
      failed: results.failed,
    });

    // 4. 返回结果
    return res.status(200).json({
      success: true,
      message: 'CSV import completed',
      results: {
        total: results.total,
        success: results.success,
        failed: results.failed,
        successRate: ((results.success / results.total) * 100).toFixed(2) + '%',
        errors: results.errors,
        details: results.details,
      },
    });
  } catch (error) {
    console.error('Error handling CSV import:', error);
    return res.status(500).json({
      success: false,
      error: error.message,
    });
  }
}

/**
 * 验证 CSV 格式（不实际导入）
 * @param {Object} req - Express request 对象
 * @param {Object} res - Express response 对象
 * @return {Promise<void>}
 */
async function validateCSV(req, res) {
  try {
    const {csvContent} = req.body;

    if (!csvContent) {
      return res.status(400).json({
        success: false,
        error: 'Missing csvContent in request body',
      });
    }

    // 解析 CSV
    const transactions = parseCSV(csvContent);

    // 返回验证结果
    return res.status(200).json({
      success: true,
      message: 'CSV validation successful',
      data: {
        totalRows: transactions.length,
        sample: transactions.slice(0, 5), // 返回前 5 条作为预览
        columns: ['date', 'amount', 'phone', 'order_id'],
      },
    });
  } catch (error) {
    console.error('Error validating CSV:', error);
    return res.status(400).json({
      success: false,
      error: error.message,
    });
  }
}

module.exports = {
  parseCSV,
  handleCSVImport,
  validateCSV,
};
