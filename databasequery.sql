-- =====================================================
-- COMPLETE SQL QUERIES FOR INVENTORY MANAGEMENT SYSTEM
-- All Operations - CRUD, Business Logic, Reports
-- =====================================================

-- =====================================================
-- 1. USER MANAGEMENT QUERIES
-- =====================================================

-- 1.1 User Authentication
-- Login user
SELECT u.user_id, u.username, u.email, u.full_name, u.phone, 
       u.branch_id, b.branch_name, b.branch_code, u.role_id, r.role_name,
       u.is_active, u.last_login
FROM users u
JOIN branches b ON u.branch_id = b.branch_id
JOIN roles r ON u.role_id = r.role_id
WHERE u.username = ? AND u.password_hash = ? AND u.is_active = TRUE;

-- Update last login
UPDATE users 
SET last_login = NOW() 
WHERE user_id = ?;

-- 1.2 User CRUD Operations
-- Create new user
INSERT INTO users (username, email, password_hash, full_name, phone, branch_id, role_id)
VALUES (?, ?, ?, ?, ?, ?, ?);

-- Get all users
SELECT u.user_id, u.username, u.email, u.full_name, u.phone,
       b.branch_name, r.role_name, u.is_active, u.created_at
FROM users u
JOIN branches b ON u.branch_id = b.branch_id
JOIN roles r ON u.role_id = r.role_id
ORDER BY u.full_name;

-- Get users by branch
SELECT u.user_id, u.username, u.full_name, r.role_name, u.is_active
FROM users u
JOIN roles r ON u.role_id = r.role_id
WHERE u.branch_id = ?
ORDER BY r.role_name, u.full_name;

-- Get user by ID
SELECT u.*, b.branch_name, r.role_name
FROM users u
JOIN branches b ON u.branch_id = b.branch_id
JOIN roles r ON u.role_id = r.role_id
WHERE u.user_id = ?;

-- Update user
UPDATE users 
SET username = ?, email = ?, full_name = ?, phone = ?, 
    branch_id = ?, role_id = ?, is_active = ?
WHERE user_id = ?;

-- Change password
UPDATE users 
SET password_hash = ? 
WHERE user_id = ?;

-- Deactivate user
UPDATE users 
SET is_active = FALSE 
WHERE user_id = ?;

-- Get user permissions (based on role)
SELECT r.role_name, r.role_description
FROM users u
JOIN roles r ON u.role_id = r.role_id
WHERE u.user_id = ?;

-- =====================================================
-- 2. BRANCH MANAGEMENT QUERIES
-- =====================================================

-- 2.1 Branch CRUD Operations
-- Get all branches
SELECT * FROM branches 
WHERE is_active = TRUE 
ORDER BY branch_name;

-- Get branch by ID
SELECT * FROM branches WHERE branch_id = ?;

-- Create new branch
INSERT INTO branches (branch_name, branch_code, city, address, phone, email, branch_manager_name)
VALUES (?, ?, ?, ?, ?, ?, ?);

-- Update branch
UPDATE branches 
SET branch_name = ?, branch_code = ?, city = ?, address = ?, 
    phone = ?, email = ?, branch_manager_name = ?
WHERE branch_id = ?;

-- Deactivate branch
UPDATE branches 
SET is_active = FALSE 
WHERE branch_id = ?;

-- Get branches for dropdown (excluding current branch for transfers)
SELECT branch_id, branch_name, branch_code
FROM branches 
WHERE is_active = TRUE AND branch_id != ?
ORDER BY branch_name;

-- =====================================================
-- 3. ITEM MANAGEMENT QUERIES
-- =====================================================

-- 3.1 Category Operations
-- Get all categories
SELECT * FROM categories ORDER BY category_name;

-- Create category
INSERT INTO categories (category_name, category_code, description)
VALUES (?, ?, ?);

-- Update category
UPDATE categories 
SET category_name = ?, description = ? 
WHERE category_id = ?;

-- 3.2 Item CRUD Operations
-- Get all items with category info
SELECT i.item_id, i.item_name, i.item_code, c.category_name, 
       i.description, i.unit_of_measure, i.minimum_stock_level,
       i.maximum_stock_level, i.unit_price, i.is_active
FROM items i
JOIN categories c ON i.category_id = c.category_id
ORDER BY i.item_name;

-- Get active items only
SELECT i.item_id, i.item_name, i.item_code, c.category_name
FROM items i
JOIN categories c ON i.category_id = c.category_id
WHERE i.is_active = TRUE
ORDER BY i.item_name;

-- Get item by ID
SELECT i.*, c.category_name
FROM items i
JOIN categories c ON i.category_id = c.category_id
WHERE i.item_id = ?;

-- Search items
SELECT i.item_id, i.item_name, i.item_code, c.category_name
FROM items i
JOIN categories c ON i.category_id = c.category_id
WHERE i.is_active = TRUE 
  AND (i.item_name LIKE CONCAT('%', ?, '%') 
       OR i.item_code LIKE CONCAT('%', ?, '%'))
ORDER BY i.item_name;

-- Create new item
INSERT INTO items (item_name, item_code, category_id, description, 
                  unit_of_measure, minimum_stock_level, maximum_stock_level, unit_price)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);

-- Update item
UPDATE items 
SET item_name = ?, item_code = ?, category_id = ?, description = ?,
    unit_of_measure = ?, minimum_stock_level = ?, maximum_stock_level = ?, unit_price = ?
WHERE item_id = ?;

-- Deactivate item
UPDATE items 
SET is_active = FALSE 
WHERE item_id = ?;

-- Get items by category
SELECT item_id, item_name, item_code, unit_of_measure
FROM items 
WHERE category_id = ? AND is_active = TRUE
ORDER BY item_name;

-- =====================================================
-- 4. INVENTORY MANAGEMENT QUERIES
-- =====================================================

-- 4.1 Stock Checking and Viewing
-- Get current stock for all items in a branch
SELECT i.item_id, i.item_name, i.item_code, c.category_name,
       COALESCE(inv.current_stock, 0) as current_stock,
       COALESCE(inv.reserved_stock, 0) as reserved_stock,
       COALESCE(inv.available_stock, 0) as available_stock,
       i.minimum_stock_level,
       CASE 
           WHEN COALESCE(inv.available_stock, 0) = 0 THEN 'OUT_OF_STOCK'
           WHEN COALESCE(inv.available_stock, 0) <= i.minimum_stock_level THEN 'LOW_STOCK'
           ELSE 'NORMAL'
       END as stock_status,
       inv.last_updated
FROM items i
JOIN categories c ON i.category_id = c.category_id
LEFT JOIN inventory inv ON i.item_id = inv.item_id AND inv.branch_id = ?
WHERE i.is_active = TRUE
ORDER BY i.item_name;

-- Check specific item stock in specific branch
SELECT i.item_name, i.item_code, b.branch_name,
       COALESCE(inv.current_stock, 0) as current_stock,
       COALESCE(inv.reserved_stock, 0) as reserved_stock,
       COALESCE(inv.available_stock, 0) as available_stock
FROM items i
CROSS JOIN branches b
LEFT JOIN inventory inv ON i.item_id = inv.item_id AND b.branch_id = inv.branch_id
WHERE i.item_id = ? AND b.branch_id = ?;

-- Get stock across all branches for an item
SELECT i.item_name, i.item_code, b.branch_name, b.branch_code,
       COALESCE(inv.current_stock, 0) as current_stock,
       COALESCE(inv.available_stock, 0) as available_stock
FROM items i
CROSS JOIN branches b
LEFT JOIN inventory inv ON i.item_id = inv.item_id AND b.branch_id = inv.branch_id
WHERE i.item_id = ? AND b.is_active = TRUE
ORDER BY b.branch_name;

-- Get low stock items for a branch
SELECT i.item_name, i.item_code, inv.available_stock, i.minimum_stock_level,
       (i.minimum_stock_level - inv.available_stock) as shortage
FROM inventory inv
JOIN items i ON inv.item_id = i.item_id
WHERE inv.branch_id = ? 
  AND inv.available_stock <= i.minimum_stock_level
  AND i.is_active = TRUE
ORDER BY shortage DESC;

-- Get out of stock items for a branch
SELECT i.item_name, i.item_code, i.minimum_stock_level
FROM items i
LEFT JOIN inventory inv ON i.item_id = inv.item_id AND inv.branch_id = ?
WHERE (inv.available_stock IS NULL OR inv.available_stock = 0)
  AND i.is_active = TRUE
ORDER BY i.item_name;

-- 4.2 Stock Updates (Manual Adjustments)
-- Add stock (Receiving new inventory)
CALL update_stock(?, ?, ?, 'IN', 'INITIAL', NULL, ?, 'Initial stock addition');

-- Adjust stock (Corrections)
CALL update_stock(?, ?, ?, 'ADJUSTMENT', 'ADJUSTMENT', NULL, ?, ?);

-- Reserve stock for transfer
UPDATE inventory 
SET reserved_stock = reserved_stock + ?
WHERE item_id = ? AND branch_id = ?;

-- Release reserved stock (if transfer cancelled)
UPDATE inventory 
SET reserved_stock = GREATEST(0, reserved_stock - ?)
WHERE item_id = ? AND branch_id = ?;

-- =====================================================
-- 5. TRANSFER REQUEST MANAGEMENT QUERIES
-- =====================================================

-- 5.1 Create Transfer Request
-- Create transfer request header
INSERT INTO transfer_requests (transfer_number, from_branch_id, to_branch_id, 
                             requested_by, priority, notes)
VALUES (generate_transfer_number(), ?, ?, ?, ?, ?);

-- Add items to transfer request
INSERT INTO transfer_request_items (transfer_id, item_id, requested_quantity, notes)
VALUES (?, ?, ?, ?);

-- 5.2 View Transfer Requests
-- Get all transfer requests (with pagination)
SELECT tr.transfer_id, tr.transfer_number, 
       fb.branch_name as from_branch, tb.branch_name as to_branch,
       u.full_name as requested_by, tr.status, tr.priority,
       tr.request_date, tr.approval_date
FROM transfer_requests tr
JOIN branches fb ON tr.from_branch_id = fb.branch_id
JOIN branches tb ON tr.to_branch_id = tb.branch_id
JOIN users u ON tr.requested_by = u.user_id
ORDER BY tr.request_date DESC
LIMIT ? OFFSET ?;

-- Get pending transfer requests for approval (from specific branch)
SELECT tr.transfer_id, tr.transfer_number, 
       tb.branch_name as to_branch, u.full_name as requested_by,
       tr.priority, tr.request_date, tr.notes,
       COUNT(tri.request_item_id) as total_items
FROM transfer_requests tr
JOIN branches tb ON tr.to_branch_id = tb.branch_id
JOIN users u ON tr.requested_by = u.user_id
LEFT JOIN transfer_request_items tri ON tr.transfer_id = tri.transfer_id
WHERE tr.from_branch_id = ? AND tr.status = 'PENDING'
GROUP BY tr.transfer_id
ORDER BY tr.priority DESC, tr.request_date;

-- Get transfer requests by status
SELECT tr.transfer_id, tr.transfer_number,
       fb.branch_name as from_branch, tb.branch_name as to_branch,
       u.full_name as requested_by, tr.request_date
FROM transfer_requests tr
JOIN branches fb ON tr.from_branch_id = fb.branch_id
JOIN branches tb ON tr.to_branch_id = tb.branch_id
JOIN users u ON tr.requested_by = u.user_id
WHERE tr.status = ?
ORDER BY tr.request_date DESC;

-- Get transfer request details
SELECT tr.*, fb.branch_name as from_branch, tb.branch_name as to_branch,
       u1.full_name as requested_by_name, u2.full_name as approved_by_name
FROM transfer_requests tr
JOIN branches fb ON tr.from_branch_id = fb.branch_id
JOIN branches tb ON tr.to_branch_id = tb.branch_id
JOIN users u1 ON tr.requested_by = u1.user_id
LEFT JOIN users u2 ON tr.approved_by = u2.user_id
WHERE tr.transfer_id = ?;

-- Get transfer request items
SELECT tri.*, i.item_name, i.item_code, i.unit_of_measure,
       COALESCE(inv.available_stock, 0) as available_stock
FROM transfer_request_items tri
JOIN items i ON tri.item_id = i.item_id
LEFT JOIN inventory inv ON i.item_id = inv.item_id 
    AND inv.branch_id = (SELECT from_branch_id FROM transfer_requests WHERE transfer_id = ?)
WHERE tri.transfer_id = ?;

-- 5.3 Transfer Request Actions
-- Approve transfer request
UPDATE transfer_requests 
SET status = 'APPROVED', approved_by = ?, approval_date = NOW()
WHERE transfer_id = ? AND status = 'PENDING';

-- Update approved quantities for items
UPDATE transfer_request_items 
SET approved_quantity = ?
WHERE transfer_id = ? AND item_id = ?;

-- Reject transfer request
UPDATE transfer_requests 
SET status = 'REJECTED', approved_by = ?, approval_date = NOW(), rejection_reason = ?
WHERE transfer_id = ? AND status = 'PENDING';

-- Cancel transfer request
UPDATE transfer_requests 
SET status = 'CANCELLED'
WHERE transfer_id = ? AND status IN ('PENDING', 'APPROVED');

-- =====================================================
-- 6. DISPATCH MANAGEMENT QUERIES
-- =====================================================

-- 6.1 Create Dispatch Slip
-- Create dispatch slip
INSERT INTO dispatch_slips (dispatch_number, transfer_id, dispatched_by, 
                          loader_name, vehicle_info, expected_delivery_date, notes)
VALUES (CONCAT('DS-', DATE_FORMAT(NOW(), '%Y%m%d'), '-', 
        LPAD((SELECT COUNT(*) + 1 FROM dispatch_slips 
              WHERE DATE(dispatch_date) = CURDATE()), 4, '0')), 
        ?, ?, ?, ?, ?, ?);

-- Update transfer status to IN_TRANSIT
UPDATE transfer_requests 
SET status = 'IN_TRANSIT', dispatch_date = NOW()
WHERE transfer_id = ?;

-- Update dispatched quantities
UPDATE transfer_request_items 
SET dispatched_quantity = approved_quantity
WHERE transfer_id = ?;

-- Reserve stock for dispatched items
UPDATE inventory inv
JOIN transfer_request_items tri ON inv.item_id = tri.item_id
SET inv.reserved_stock = inv.reserved_stock + tri.approved_quantity
WHERE inv.branch_id = (SELECT from_branch_id FROM transfer_requests WHERE transfer_id = ?)
  AND tri.transfer_id = ?;

-- Reduce actual stock for dispatched items
-- This should be done item by item using the stored procedure
-- CALL update_stock(item_id, from_branch_id, approved_quantity, 'TRANSFER_OUT', 'TRANSFER', transfer_id, user_id, 'Dispatched to branch');

-- 6.2 View Dispatch Information
-- Get dispatch slips
SELECT ds.*, tr.transfer_number, tb.branch_name as to_branch, u.full_name as dispatched_by_name
FROM dispatch_slips ds
JOIN transfer_requests tr ON ds.transfer_id = tr.transfer_id
JOIN branches tb ON tr.to_branch_id = tb.branch_id
JOIN users u ON ds.dispatched_by = u.user_id
ORDER BY ds.dispatch_date DESC;

-- Get dispatch details
SELECT ds.*, tr.transfer_number, 
       fb.branch_name as from_branch, tb.branch_name as to_branch
FROM dispatch_slips ds
JOIN transfer_requests tr ON ds.transfer_id = tr.transfer_id
JOIN branches fb ON tr.from_branch_id = fb.branch_id
JOIN branches tb ON tr.to_branch_id = tb.branch_id
WHERE ds.dispatch_id = ?;

-- Get items in dispatch
SELECT tri.item_id, i.item_name, i.item_code, tri.dispatched_quantity, i.unit_of_measure
FROM transfer_request_items tri
JOIN items i ON tri.item_id = i.item_id
JOIN dispatch_slips ds ON tri.transfer_id = ds.transfer_id
WHERE ds.dispatch_id = ?;

-- =====================================================
-- 7. RECEIVING MANAGEMENT QUERIES
-- =====================================================

-- 7.1 Create Receiving Slip
-- Create receiving slip
INSERT INTO receiving_slips (receiving_number, transfer_id, dispatch_id, received_by, 
                           condition_on_arrival, notes, photo_path)
VALUES (CONCAT('RS-', DATE_FORMAT(NOW(), '%Y%m%d'), '-', 
        LPAD((SELECT COUNT(*) + 1 FROM receiving_slips 
              WHERE DATE(receiving_date) = CURDATE()), 4, '0')), 
        ?, ?, ?, ?, ?, ?);

-- Add received items details
INSERT INTO receiving_slip_items (receiving_id, item_id, dispatched_quantity, 
                                received_quantity, damaged_quantity, condition_notes)
VALUES (?, ?, ?, ?, ?, ?);

-- Update transfer status to DELIVERED
UPDATE transfer_requests 
SET status = 'DELIVERED', delivery_date = NOW()
WHERE transfer_id = ?;

-- Update received quantities in transfer request items
UPDATE transfer_request_items 
SET received_quantity = ?
WHERE transfer_id = ? AND item_id = ?;

-- Add stock to receiving branch
-- CALL update_stock(item_id, to_branch_id, received_quantity, 'TRANSFER_IN', 'TRANSFER', transfer_id, user_id, 'Received from branch');

-- Release reserved stock from sending branch
UPDATE inventory inv
JOIN transfer_request_items tri ON inv.item_id = tri.item_id
SET inv.reserved_stock = GREATEST(0, inv.reserved_stock - tri.received_quantity)
WHERE inv.branch_id = (SELECT from_branch_id FROM transfer_requests WHERE transfer_id = ?)
  AND tri.transfer_id = ?;

-- 7.2 View Receiving Information
-- Get receiving slips
SELECT rs.*, tr.transfer_number, fb.branch_name as from_branch, u.full_name as received_by_name
FROM receiving_slips rs
JOIN transfer_requests tr ON rs.transfer_id = tr.transfer_id
JOIN branches fb ON tr.from_branch_id = fb.branch_id
JOIN users u ON rs.received_by = u.user_id
ORDER BY rs.receiving_date DESC;

-- Get receiving details
SELECT rs.*, tr.transfer_number, ds.dispatch_number,
       fb.branch_name as from_branch, tb.branch_name as to_branch
FROM receiving_slips rs
JOIN transfer_requests tr ON rs.transfer_id = tr.transfer_id
JOIN dispatch_slips ds ON rs.dispatch_id = ds.dispatch_id
JOIN branches fb ON tr.from_branch_id = fb.branch_id
JOIN branches tb ON tr.to_branch_id = tb.branch_id
WHERE rs.receiving_id = ?;

-- Get received items details
SELECT rsi.*, i.item_name, i.item_code, i.unit_of_measure
FROM receiving_slip_items rsi
JOIN items i ON rsi.item_id = i.item_id
WHERE rsi.receiving_id = ?;

-- =====================================================
-- 8. STOCK MOVEMENT HISTORY QUERIES
-- =====================================================

-- Get all stock movements for an item
SELECT sm.*, i.item_name, b.branch_name, u.full_name as created_by_name
FROM stock_movements sm
JOIN items i ON sm.item_id = i.item_id
JOIN branches b ON sm.branch_id = b.branch_id
JOIN users u ON sm.created_by = u.user_id
WHERE sm.item_id = ?
ORDER BY sm.created_at DESC;

-- Get stock movements for a branch
SELECT sm.*, i.item_name, i.item_code, u.full_name as created_by_name
FROM stock_movements sm
JOIN items i ON sm.item_id = i.item_id
JOIN users u ON sm.created_by = u.user_id
WHERE sm.branch_id = ?
ORDER BY sm.created_at DESC
LIMIT ? OFFSET ?;

-- Get stock movements by date range
SELECT sm.*, i.item_name, b.branch_name, u.full_name as created_by_name
FROM stock_movements sm
JOIN items i ON sm.item_id = i.item_id
JOIN branches b ON sm.branch_id = b.branch_id
JOIN users u ON sm.created_by = u.user_id
WHERE sm.created_at BETWEEN ? AND ?
ORDER BY sm.created_at DESC;

-- Get stock movements by type
SELECT sm.*, i.item_name, b.branch_name, u.full_name as created_by_name
FROM stock_movements sm
JOIN items i ON sm.item_id = i.item_id
JOIN branches b ON sm.branch_id = b.branch_id
JOIN users u ON sm.created_by = u.user_id
WHERE sm.movement_type = ?
ORDER BY sm.created_at DESC;

-- =====================================================
-- 9. REPORTING QUERIES
-- =====================================================

-- 9.1 Stock Reports
-- Current stock summary by branch
SELECT b.branch_name, 
       COUNT(DISTINCT inv.item_id) as total_items,
       SUM(inv.current_stock) as total_stock,
       SUM(inv.reserved_stock) as total_reserved,
       SUM(inv.available_stock) as total_available,
       SUM(CASE WHEN inv.available_stock <= i.minimum_stock_level THEN 1 ELSE 0 END) as low_stock_items,
       SUM(CASE WHEN inv.available_stock = 0 THEN 1 ELSE 0 END) as out_of_stock_items
FROM branches b
LEFT JOIN inventory inv ON b.branch_id = inv.branch_id
LEFT JOIN items i ON inv.item_id = i.item_id AND i.is_active = TRUE
WHERE b.is_active = TRUE
GROUP BY b.branch_id, b.branch_name
ORDER BY b.branch_name;

-- Stock valuation report
SELECT b.branch_name, i.item_name, inv.current_stock, i.unit_price,
       (inv.current_stock * i.unit_price) as total_value
FROM inventory inv
JOIN items i ON inv.item_id = i.item_id
JOIN branches b ON inv.branch_id = b.branch_id
WHERE i.is_active = TRUE AND b.is_active = TRUE
ORDER BY total_value DESC;

-- Stock aging report (items that haven't moved recently)
SELECT i.item_name, b.branch_name, inv.current_stock,
       COALESCE(MAX(sm.created_at), inv.last_updated) as last_movement,
       DATEDIFF(NOW(), COALESCE(MAX(sm.created_at), inv.last_updated)) as days_since_movement
FROM inventory inv
JOIN items i ON inv.item_id = i.item_id
JOIN branches b ON inv.branch_id = b.branch_id
LEFT JOIN stock_movements sm ON inv.item_id = sm.item_id AND inv.branch_id = sm.branch_id
WHERE i.is_active = TRUE AND inv.current_stock > 0
GROUP BY inv.item_id, inv.branch_id
HAVING days_since_movement > 90
ORDER BY days_since_movement DESC;

-- 9.2 Transfer Reports
-- Transfer summary by period
SELECT DATE(tr.request_date) as request_date,
       COUNT(*) as total_requests,
       SUM(CASE WHEN tr.status = 'PENDING' THEN 1 ELSE 0 END) as pending,
       SUM(CASE WHEN tr.status = 'APPROVED' THEN 1 ELSE 0 END) as approved,
       SUM(CASE WHEN tr.status = 'DELIVERED' THEN 1 ELSE 0 END) as completed,
       SUM(CASE WHEN tr.status = 'REJECTED' THEN 1 ELSE 0 END) as rejected
FROM transfer_requests tr
WHERE tr.request_date BETWEEN ? AND ?
GROUP BY DATE(tr.request_date)
ORDER BY request_date DESC;

-- Most requested items
SELECT i.item_name, COUNT(*) as request_count, SUM(tri.requested_quantity) as total_requested
FROM transfer_request_items tri
JOIN items i ON tri.item_id = i.item_id
JOIN transfer_requests tr ON tri.transfer_id = tr.transfer_id
WHERE tr.request_date BETWEEN ? AND ?
GROUP BY i.item_id, i.item_name
ORDER BY request_count DESC, total_requested DESC;

-- Transfer performance (average processing time)
SELECT fb.branch_name as from_branch, tb.branch_name as to_branch,
       COUNT(*) as total_transfers,
       AVG(DATEDIFF(tr.approval_date, tr.request_date)) as avg_approval_days,
       AVG(DATEDIFF(tr.dispatch_date, tr.approval_date)) as avg_dispatch_days,
       AVG(DATEDIFF(tr.delivery_date, tr.dispatch_date)) as avg_delivery_days,
       AVG(DATEDIFF(tr.delivery_date, tr.request_date)) as avg_total_days
FROM transfer_requests tr
JOIN branches fb ON tr.from_branch_id = fb.branch_id
JOIN branches tb ON tr.to_branch_id = tb.branch_id
WHERE tr.status = 'DELIVERED' 
  AND tr.request_date BETWEEN ? AND ?
GROUP BY tr.from_branch_id, tr.to_branch_id
ORDER BY avg_total_days DESC;

-- 9.3 User Activity Reports
-- User activity summary
SELECT u.full_name, b.branch_name, r.role_name,
       COUNT(DISTINCT tr.transfer_id) as transfer_requests,
       COUNT(DISTINCT ds.dispatch_id) as dispatches,
       COUNT(DISTINCT rs.receiving_id) as receipts,
       COUNT(DISTINCT sm.movement_id) as stock_movements
FROM users u
JOIN branches b ON u.branch_id = b.branch_id
JOIN roles r ON u.role_id = r.role_id
LEFT JOIN transfer_requests tr ON u.user_id = tr.requested_by
LEFT JOIN dispatch_slips ds ON u.user_id = ds.dispatched_by
LEFT JOIN receiving_slips rs ON u.user_id = rs.received_by
LEFT JOIN stock_movements sm ON u.user_id = sm.created_by
WHERE u.is_active = TRUE
GROUP BY u.user_id
ORDER BY b.branch_name, u.full_name;

-- System logs for audit
SELECT sl.*, u.full_name as user_name
FROM system_logs sl
LEFT JOIN users u ON sl.user_id = u.user_id
WHERE sl.created_at BETWEEN ? AND ?
ORDER BY sl.created_at DESC
LIMIT ? OFFSET ?;

-- =====================================================
-- 10. DASHBOARD QUERIES
-- =====================================================

-- Dashboard summary for a branch
SELECT 
    (SELECT COUNT(*) FROM inventory WHERE branch_id = ? AND available_stock > 0) as items_in_stock,
    (SELECT COUNT(*) FROM inventory inv JOIN items i ON inv.item_id = i.item_id 
     WHERE inv.branch_id = ? AND inv.available_stock <= i.minimum_stock_level) as low_stock_items,
    (SELECT COUNT(*) FROM transfer_requests WHERE to_branch_id = ? AND status = 'PENDING') as pending_requests,
    (SELECT COUNT(*) FROM transfer_requests WHERE from_branch_id = ? AND status = 'APPROVED') as pending_dispatches,
    (SELECT COUNT(*) FROM transfer_requests WHERE to_branch_id = ? AND status = 'IN_TRANSIT') as incoming_shipments;

-- Recent activities for dashboard
SELECT 'TRANSFER_REQUEST' as activity_type, tr.transfer_number as reference,
       CONCAT('Transfer request from ', fb.branch_name, ' to ', tb.branch_name) as description,
       tr.request_date as activity_date
FROM transfer_requests tr
JOIN branches fb ON tr.from_branch_id = fb.branch_id
JOIN branches tb ON tr.to_branch_id = tb.branch_id
WHERE tr.from_branch_id = ? OR tr.to_branch_id = ?
UNION ALL
SELECT 'STOCK_MOVEMENT' as activity_type, CONCAT('SM-', sm.movement_id) as reference,
       CONCAT(sm.movement_type, ' - ', i.item_name, ' (', sm.quantity, ')') as description,
       sm.created_at as activity_date
FROM stock_movements sm
JOIN items i ON sm.item_id = i.item_id
WHERE sm.branch_id = ?
ORDER BY activity_date DESC
LIMIT 10;

-- =====================================================
-- 11. SEARCH AND FILTER QUERIES
-- =====================================================

-- Advanced search for transfer requests
SELECT tr.transfer_id, tr.transfer_number, tr.status, tr.priority,
       fb.branch_name as from_branch, tb.branch_name as to_branch,
       u.full_name as requested_by, tr.request_date
FROM transfer_requests tr
JOIN branches fb ON tr.from_branch_id = fb.branch_id
JOIN branches tb ON tr.to_branch_id = tb.branch_id
JOIN users u ON tr.requested_by = u.user_id
WHERE (? IS NULL OR tr.status = ?)
  AND (? IS NULL OR tr.from_branch_id = ?)
  AND (? IS NULL OR tr.to_branch_id = ?)
  AND (? IS NULL OR tr.priority = ?)
  AND (? IS NULL OR tr.request_date >= ?)
  AND (? IS NULL OR tr.request_date <= ?)
ORDER BY tr.request_date DESC;

-- Search stock movements with filters
SELECT sm.*, i.item_name, b.branch_name, u.full_name as created_by_name
FROM stock_movements sm
JOIN items i ON sm.item_id = i.item_id
JOIN branches b ON sm.branch_id = b.branch_id
JOIN users u ON sm.created_by = u.user_id
WHERE (? IS NULL OR sm.item_id = ?)
  AND (? IS NULL OR sm.branch_id = ?)
  AND (? IS NULL OR sm.movement_type = ?)
  AND (? IS NULL OR sm.created_at >= ?)
  AND (? IS NULL OR sm.created_at <= ?)
ORDER BY sm.created_at DESC;

-- =====================================================
-- 12. UTILITY QUERIES
-- =====================================================

-- Generate next transfer number
SELECT generate_transfer_number() as next_transfer_number;

-- Check item availability before transfer
SELECT i.item_name, i.item_code, inv.available_stock,
       CASE WHEN inv.available_stock >= ? THEN 'AVAILABLE' ELSE 'INSUFFICIENT' END as availability_status
FROM items i
LEFT JOIN inventory inv ON i.item_id = inv.item_id AND inv.branch_id = ?
WHERE i.item_id = ?;

-- Get system statistics
SELECT 
    (SELECT COUNT(*) FROM branches WHERE is_active = TRUE) as total_branches,
    (SELECT COUNT(*) FROM users WHERE is_active = TRUE) as total_users,
    (SELECT COUNT(*) FROM items WHERE is_active = TRUE) as total_items,
    (SELECT COUNT(*) FROM transfer_requests WHERE status = 'PENDING') as pending_transfers,
    (SELECT SUM(current_stock) FROM inventory) as total_stock_units;

-- Database cleanup queries
DELETE FROM system_logs WHERE created_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);

-- =====================================================
-- 13. STOCK DISCREPANCY MANAGEMENT QUERIES
-- =====================================================

-- Report stock discrepancy
INSERT INTO stock_discrepancies (branch_id, item_id, expected_stock, actual_stock, 
                                difference, discrepancy_type, reported_by, investigation_notes)
VALUES (?, ?, ?, ?, ?, ?, ?, ?);

-- Get all discrepancies
SELECT sd.*, i.item_name, b.branch_name, u.full_name as reported_by_name
FROM stock_discrepancies sd
JOIN items i ON sd.item_id = i.item_id
JOIN branches b ON sd.branch_id = b.branch_id
JOIN users u ON sd.reported_by = u.user_id
ORDER BY sd.reported_date DESC;

-- Get pending discrepancies for investigation
SELECT sd.*, i.item_name, i.item_code, b.branch_name
FROM stock_discrepancies sd
JOIN items i ON sd.item_id = i.item_id
JOIN branches b ON sd.branch_id = b.branch_id
WHERE sd.status = 'REPORTED'
ORDER BY ABS(sd.difference) DESC;

-- Update discrepancy investigation
UPDATE stock_discrepancies 
SET status = 'INVESTIGATING', investigation_notes = ?
WHERE discrepancy_id = ?;

-- Resolve discrepancy
UPDATE stock_discrepancies 
SET status = 'RESOLVED', resolution_notes = ?, resolved_date = NOW()
WHERE discrepancy_id = ?;

-- =====================================================
-- 14. BATCH OPERATIONS QUERIES
-- =====================================================

-- Bulk update minimum stock levels
UPDATE items 
SET minimum_stock_level = ? 
WHERE category_id = ?;

-- Bulk price update by category
UPDATE items 
SET unit_price = unit_price * (1 + ? / 100) 
WHERE category_id = ?;

-- Bulk transfer approval for low priority items
UPDATE transfer_requests 
SET status = 'APPROVED', approved_by = ?, approval_date = NOW()
WHERE status = 'PENDING' AND priority = 'LOW' AND from_branch_id = ?;

-- Bulk stock adjustment for physical count
INSERT INTO stock_movements (item_id, branch_id, movement_type, quantity, 
                           previous_stock, new_stock, reference_type, notes, created_by)
SELECT inv.item_id, inv.branch_id, 'ADJUSTMENT',
       (? - inv.current_stock) as quantity,
       inv.current_stock as previous_stock,
       ? as new_stock,
       'ADJUSTMENT' as reference_type,
       'Physical count adjustment' as notes,
       ? as created_by
FROM inventory inv
WHERE inv.item_id = ? AND inv.branch_id = ? AND inv.current_stock != ?;

-- Update inventory after bulk adjustment
UPDATE inventory 
SET current_stock = ?, updated_by = ?
WHERE item_id = ? AND branch_id = ?;

-- =====================================================
-- 15. ADVANCED REPORTING QUERIES
-- =====================================================

-- Monthly stock movement summary
SELECT YEAR(sm.created_at) as year, MONTH(sm.created_at) as month,
       sm.movement_type, COUNT(*) as movement_count, SUM(sm.quantity) as total_quantity
FROM stock_movements sm
WHERE sm.created_at BETWEEN ? AND ?
GROUP BY YEAR(sm.created_at), MONTH(sm.created_at), sm.movement_type
ORDER BY year DESC, month DESC, sm.movement_type;

-- Branch performance comparison
SELECT b.branch_name,
       COUNT(DISTINCT tr_out.transfer_id) as transfers_sent,
       COUNT(DISTINCT tr_in.transfer_id) as transfers_received,
       AVG(CASE WHEN tr_out.status = 'DELIVERED' 
           THEN DATEDIFF(tr_out.delivery_date, tr_out.request_date) END) as avg_fulfillment_days,
       SUM(CASE WHEN tr_out.status = 'REJECTED' THEN 1 ELSE 0 END) as rejections_sent
FROM branches b
LEFT JOIN transfer_requests tr_out ON b.branch_id = tr_out.from_branch_id
LEFT JOIN transfer_requests tr_in ON b.branch_id = tr_in.to_branch_id
WHERE b.is_active = TRUE
GROUP BY b.branch_id, b.branch_name
ORDER BY avg_fulfillment_days;

-- Item demand analysis
SELECT i.item_name, i.item_code,
       COUNT(DISTINCT tri.transfer_id) as times_requested,
       SUM(tri.requested_quantity) as total_requested,
       AVG(tri.requested_quantity) as avg_requested_per_transfer,
       COUNT(DISTINCT tr.to_branch_id) as requesting_branches
FROM items i
JOIN transfer_request_items tri ON i.item_id = tri.item_id
JOIN transfer_requests tr ON tri.transfer_id = tr.transfer_id
WHERE tr.request_date BETWEEN ? AND ?
GROUP BY i.item_id, i.item_name, i.item_code
ORDER BY times_requested DESC, total_requested DESC;

-- Seasonal demand patterns
SELECT i.item_name, MONTH(tr.request_date) as month, 
       COUNT(*) as requests, SUM(tri.requested_quantity) as total_quantity
FROM items i
JOIN transfer_request_items tri ON i.item_id = tri.item_id
JOIN transfer_requests tr ON tri.transfer_id = tr.transfer_id
WHERE tr.request_date BETWEEN DATE_SUB(NOW(), INTERVAL 1 YEAR) AND NOW()
GROUP BY i.item_id, i.item_name, MONTH(tr.request_date)
ORDER BY i.item_name, month;

-- Stock turnover analysis
SELECT i.item_name, b.branch_name,
       inv.current_stock,
       COALESCE(SUM(CASE WHEN sm.movement_type = 'OUT' THEN sm.quantity ELSE 0 END), 0) as total_outgoing,
       CASE 
           WHEN inv.current_stock > 0 AND SUM(CASE WHEN sm.movement_type = 'OUT' THEN sm.quantity ELSE 0 END) > 0
           THEN ROUND(SUM(CASE WHEN sm.movement_type = 'OUT' THEN sm.quantity ELSE 0 END) / inv.current_stock, 2)
           ELSE 0 
       END as turnover_ratio
FROM inventory inv
JOIN items i ON inv.item_id = i.item_id
JOIN branches b ON inv.branch_id = b.branch_id
LEFT JOIN stock_movements sm ON inv.item_id = sm.item_id 
    AND inv.branch_id = sm.branch_id 
    AND sm.created_at BETWEEN DATE_SUB(NOW(), INTERVAL 3 MONTH) AND NOW()
WHERE i.is_active = TRUE AND inv.current_stock > 0
GROUP BY inv.item_id, inv.branch_id, i.item_name, b.branch_name, inv.current_stock
ORDER BY turnover_ratio DESC;

-- =====================================================
-- 16. NOTIFICATION AND ALERT QUERIES
-- =====================================================

-- Get items needing reorder (below minimum stock)
SELECT i.item_name, i.item_code, b.branch_name, 
       inv.available_stock, i.minimum_stock_level,
       (i.minimum_stock_level - inv.available_stock) as reorder_quantity
FROM inventory inv
JOIN items i ON inv.item_id = i.item_id
JOIN branches b ON inv.branch_id = b.branch_id
WHERE inv.available_stock < i.minimum_stock_level
  AND i.is_active = TRUE
ORDER BY reorder_quantity DESC;

-- Get overdue transfers (not delivered within expected time)
SELECT tr.transfer_number, fb.branch_name as from_branch, tb.branch_name as to_branch,
       tr.request_date, ds.expected_delivery_date,
       DATEDIFF(NOW(), ds.expected_delivery_date) as days_overdue
FROM transfer_requests tr
JOIN branches fb ON tr.from_branch_id = fb.branch_id
JOIN branches tb ON tr.to_branch_id = tb.branch_id
JOIN dispatch_slips ds ON tr.transfer_id = ds.transfer_id
WHERE tr.status = 'IN_TRANSIT' 
  AND ds.expected_delivery_date < CURDATE()
ORDER BY days_overdue DESC;

-- Get pending approvals older than 24 hours
SELECT tr.transfer_number, tb.branch_name as requesting_branch,
       u.full_name as requested_by, tr.request_date, tr.priority,
       TIMESTAMPDIFF(HOUR, tr.request_date, NOW()) as hours_pending
FROM transfer_requests tr
JOIN branches tb ON tr.to_branch_id = tb.branch_id
JOIN users u ON tr.requested_by = u.user_id
WHERE tr.status = 'PENDING' 
  AND tr.request_date < DATE_SUB(NOW(), INTERVAL 1 DAY)
ORDER BY hours_pending DESC;

-- Get users who haven't logged in recently
SELECT u.full_name, u.username, b.branch_name, u.last_login,
       DATEDIFF(NOW(), u.last_login) as days_since_login
FROM users u
JOIN branches b ON u.branch_id = b.branch_id
WHERE u.is_active = TRUE
  AND (u.last_login IS NULL OR u.last_login < DATE_SUB(NOW(), INTERVAL 7 DAY))
ORDER BY days_since_login DESC;

-- =====================================================
-- 17. DATA VALIDATION QUERIES
-- =====================================================

-- Check for negative stock (data integrity issue)
SELECT i.item_name, b.branch_name, inv.current_stock
FROM inventory inv
JOIN items i ON inv.item_id = i.item_id
JOIN branches b ON inv.branch_id = b.branch_id
WHERE inv.current_stock < 0;

-- Check for reserved stock greater than current stock
SELECT i.item_name, b.branch_name, inv.current_stock, inv.reserved_stock
FROM inventory inv
JOIN items i ON inv.item_id = i.item_id
JOIN branches b ON inv.branch_id = b.branch_id
WHERE inv.reserved_stock > inv.current_stock;

-- Check for orphaned transfer request items
SELECT tri.transfer_id, tri.item_id
FROM transfer_request_items tri
LEFT JOIN transfer_requests tr ON tri.transfer_id = tr.transfer_id
WHERE tr.transfer_id IS NULL;

-- Validate stock movements against inventory
SELECT sm.movement_id, i.item_name, b.branch_name, sm.new_stock, inv.current_stock
FROM stock_movements sm
JOIN items i ON sm.item_id = i.item_id
JOIN branches b ON sm.branch_id = b.branch_id
JOIN inventory inv ON sm.item_id = inv.item_id AND sm.branch_id = inv.branch_id
WHERE sm.new_stock != inv.current_stock
  AND sm.created_at = (SELECT MAX(created_at) FROM stock_movements 
                      WHERE item_id = sm.item_id AND branch_id = sm.branch_id);

-- =====================================================
-- 18. MAINTENANCE QUERIES
-- =====================================================

-- Cleanup old system logs (keep last 6 months)
DELETE FROM system_logs 
WHERE created_at < DATE_SUB(NOW(), INTERVAL 6 MONTH);

-- Archive completed transfers older than 1 year
-- Note: You might want to create an archive table first
CREATE TABLE archived_transfers AS
SELECT * FROM transfer_requests 
WHERE status = 'DELIVERED' 
  AND delivery_date < DATE_SUB(NOW(), INTERVAL 1 YEAR);

-- Update stock levels based on actual movements (reconciliation)
UPDATE inventory inv
SET current_stock = (
    SELECT COALESCE(SUM(
        CASE 
            WHEN sm.movement_type IN ('IN', 'TRANSFER_IN') THEN sm.quantity
            WHEN sm.movement_type IN ('OUT', 'TRANSFER_OUT') THEN -sm.quantity
            WHEN sm.movement_type = 'ADJUSTMENT' THEN sm.quantity
            ELSE 0
        END
    ), 0)
    FROM stock_movements sm
    WHERE sm.item_id = inv.item_id AND sm.branch_id = inv.branch_id
)
WHERE inv.item_id = ? AND inv.branch_id = ?;

-- Reset reserved stock for cancelled transfers
UPDATE inventory inv
SET reserved_stock = (
    SELECT COALESCE(SUM(tri.approved_quantity - tri.dispatched_quantity), 0)
    FROM transfer_request_items tri
    JOIN transfer_requests tr ON tri.transfer_id = tr.transfer_id
    WHERE tr.from_branch_id = inv.branch_id
      AND inv.item_id = tri.item_id
      AND tr.status IN ('APPROVED', 'IN_TRANSIT')
);

-- =====================================================
-- 19. BACKUP AND EXPORT QUERIES
-- =====================================================

-- Export current inventory for backup
SELECT b.branch_code, i.item_code, inv.current_stock, inv.reserved_stock, 
       inv.last_updated, u.username as updated_by
FROM inventory inv
JOIN items i ON inv.item_id = i.item_id
JOIN branches b ON inv.branch_id = b.branch_id
LEFT JOIN users u ON inv.updated_by = u.user_id
ORDER BY b.branch_code, i.item_code;

-- Export all transfer requests for audit
SELECT tr.transfer_number, tr.status, tr.priority,
       fb.branch_code as from_branch, tb.branch_code as to_branch,
       ur.username as requested_by, ua.username as approved_by,
       tr.request_date, tr.approval_date, tr.dispatch_date, tr.delivery_date
FROM transfer_requests tr
JOIN branches fb ON tr.from_branch_id = fb.branch_id
JOIN branches tb ON tr.to_branch_id = tb.branch_id
JOIN users ur ON tr.requested_by = ur.user_id
LEFT JOIN users ua ON tr.approved_by = ua.user_id
WHERE tr.request_date BETWEEN ? AND ?
ORDER BY tr.request_date;

-- Export stock movement summary for accounting
SELECT DATE(sm.created_at) as movement_date,
       i.item_code, b.branch_code, sm.movement_type,
       sm.quantity, sm.reference_type, u.username as created_by
FROM stock_movements sm
JOIN items i ON sm.item_id = i.item_id
JOIN branches b ON sm.branch_id = b.branch_id
JOIN users u ON sm.created_by = u.user_id
WHERE sm.created_at BETWEEN ? AND ?
ORDER BY sm.created_at;

-- =====================================================
-- 20. PERFORMANCE MONITORING QUERIES
-- =====================================================

-- Check table sizes and row counts
SELECT 
    'branches' as table_name, COUNT(*) as row_count FROM branches
UNION ALL SELECT 'users', COUNT(*) FROM users
UNION ALL SELECT 'items', COUNT(*) FROM items
UNION ALL SELECT 'inventory', COUNT(*) FROM inventory
UNION ALL SELECT 'transfer_requests', COUNT(*) FROM transfer_requests
UNION ALL SELECT 'transfer_request_items', COUNT(*) FROM transfer_request_items
UNION ALL SELECT 'stock_movements', COUNT(*) FROM stock_movements
UNION ALL SELECT 'dispatch_slips', COUNT(*) FROM dispatch_slips
UNION ALL SELECT 'receiving_slips', COUNT(*) FROM receiving_slips
UNION ALL SELECT 'system_logs', COUNT(*) FROM system_logs;

-- Monitor slow queries (indexes effectiveness)
EXPLAIN SELECT i.item_name, b.branch_name, inv.available_stock
FROM inventory inv
JOIN items i ON inv.item_id = i.item_id
JOIN branches b ON inv.branch_id = b.branch_id
WHERE inv.available_stock <= i.minimum_stock_level;

-- Check for missing indexes
SHOW INDEX FROM inventory;
SHOW INDEX FROM stock_movements;
SHOW INDEX FROM transfer_requests;

-- =====================================================
-- 21. MOBILE APP SPECIFIC QUERIES
-- =====================================================

-- Quick stock check for mobile (lightweight)
SELECT i.item_code, i.item_name, inv.available_stock
FROM inventory inv
JOIN items i ON inv.item_id = i.item_id
WHERE inv.branch_id = ? AND i.item_code = ?;

-- Mobile dashboard summary
SELECT 
    COUNT(CASE WHEN inv.available_stock <= i.minimum_stock_level THEN 1 END) as low_stock_count,
    COUNT(CASE WHEN tr.status = 'PENDING' AND tr.to_branch_id = ? THEN 1 END) as pending_requests,
    COUNT(CASE WHEN tr.status = 'IN_TRANSIT' AND tr.to_branch_id = ? THEN 1 END) as incoming_shipments
FROM inventory inv
JOIN items i ON inv.item_id = i.item_id
CROSS JOIN transfer_requests tr
WHERE inv.branch_id = ?;

-- QR code/Barcode scanner query
SELECT i.item_id, i.item_name, i.item_code, c.category_name,
       COALESCE(inv.available_stock, 0) as available_stock
FROM items i
JOIN categories c ON i.category_id = c.category_id
LEFT JOIN inventory inv ON i.item_id = inv.item_id AND inv.branch_id = ?
WHERE i.item_code = ? AND i.is_active = TRUE;

-- =====================================================
-- 22. API ENDPOINT QUERIES
-- =====================================================

-- REST API: GET /branches
SELECT branch_id, branch_name, branch_code, city
FROM branches 
WHERE is_active = TRUE 
ORDER BY branch_name;

-- REST API: GET /items/search?q=camera
SELECT item_id, item_name, item_code, unit_of_measure
FROM items 
WHERE is_active = TRUE 
  AND (item_name LIKE CONCAT('%', ?, '%') OR item_code LIKE CONCAT('%', ?, '%'))
LIMIT 20;

-- REST API: GET /inventory/branch/:id
SELECT i.item_id, i.item_name, i.item_code, 
       COALESCE(inv.available_stock, 0) as stock,
       i.minimum_stock_level
FROM items i
LEFT JOIN inventory inv ON i.item_id = inv.item_id AND inv.branch_id = ?
WHERE i.is_active = TRUE
ORDER BY i.item_name;

-- REST API: POST /transfers (create transfer request)
-- This would use the previous CREATE transfer queries

-- REST API: GET /transfers/pending
SELECT tr.transfer_id, tr.transfer_number, tb.branch_name as to_branch,
       u.full_name as requested_by, tr.request_date, tr.priority
FROM transfer_requests tr
JOIN branches tb ON tr.to_branch_id = tb.branch_id
JOIN users u ON tr.requested_by = u.user_id
WHERE tr.from_branch_id = ? AND tr.status = 'PENDING'
ORDER BY tr.priority DESC, tr.request_date;

-- =====================================================
-- 23. SECURITY AND PERMISSION QUERIES
-- =====================================================

-- Check user permissions for specific action
SELECT r.role_name, u.branch_id
FROM users u
JOIN roles r ON u.role_id = r.role_id
WHERE u.user_id = ? AND u.is_active = TRUE;

-- Log user action for audit
INSERT INTO system_logs (user_id, action, table_affected, record_id, ip_address, user_agent)
VALUES (?, ?, ?, ?, ?, ?);

-- Check if user can access specific branch data
SELECT 1 FROM users 
WHERE user_id = ? 
  AND (branch_id = ? OR role_id IN (1)) -- Admin can access all branches
  AND is_active = TRUE;

-- Session management
UPDATE users SET last_login = NOW() WHERE user_id = ?;

-- Password reset token (if implementing)
-- You would typically add a password_reset_tokens table
-- UPDATE users SET password_reset_token = ?, token_expires = DATE_ADD(NOW(), INTERVAL 1 HOUR) WHERE email = ?;

-- =====================================================
-- FINAL NOTES ON USAGE
-- =====================================================

/*
PARAMETER PLACEHOLDERS:
All queries use ? as parameter placeholders for prepared statements.
Replace these with actual values when implementing in your application.

TRANSACTION EXAMPLES:
For operations that need to be atomic (like stock transfers):

START TRANSACTION;
-- Execute multiple related queries
-- If any fails, ROLLBACK; otherwise COMMIT;

STORED PROCEDURE CALLS:
CALL update_stock(item_id, branch_id, quantity, movement_type, reference_type, reference_id, user_id, notes);

INDEX USAGE:
The database schema includes proper indexes. Monitor query performance and add additional indexes as needed.

SECURITY:
- Always use prepared statements
- Validate user permissions before executing queries  
- Log sensitive operations
- Hash passwords properly (bcrypt recommended)

ERROR HANDLING:
Implement proper error handling for:
- Constraint violations
- Deadlocks in concurrent operations
- Data validation failures

PAGINATION:
Many list queries include LIMIT and OFFSET for pagination.
Always implement pagination for large datasets.
*/