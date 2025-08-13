# API Development Guide - Table Dependencies & Implementation Order

## 🏗️ **Database Table Hierarchy & Dependencies**

### **Level 1: Foundation Tables (Start Here)**
These tables have no foreign key dependencies and should be implemented first:

1. **`roles`** - User roles (Admin, Manager, etc.)
2. **`branches`** - Company locations  
3. **`categories`** - Item categories

### **Level 2: Core Tables**
These depend on Level 1 tables:

4. **`users`** - Depends on: `branches`, `roles`
5. **`items`** - Depends on: `categories`

### **Level 3: Inventory Tables**
These depend on Level 2 tables:

6. **`inventory`** - Depends on: `items`, `branches`, `users`
7. **`stock_movements`** - Depends on: `items`, `branches`, `users`

### **Level 4: Business Process Tables**
These depend on multiple previous levels:

8. **`transfer_requests`** - Depends on: `branches`, `users`
9. **`transfer_request_items`** - Depends on: `transfer_requests`, `items`
10. **`dispatch_slips`** - Depends on: `transfer_requests`, `users`
11. **`receiving_slips`** - Depends on: `transfer_requests`, `dispatch_slips`, `users`
12. **`receiving_slip_items`** - Depends on: `receiving_slips`, `items`

### **Level 5: Support Tables**
These are used for logging and reporting:

13. **`stock_discrepancies`** - Depends on: `branches`, `items`, `users`
14. **`system_logs`** - Depends on: `users`

---

## 🚀 **Recommended API Development Order**

### **Phase 1: Foundation APIs** ⭐ **START HERE**

#### 1. **Branches API** (`branches` table)
```
GET    /api/branches           - List all branches
GET    /api/branches/:id       - Get branch details
POST   /api/branches           - Create branch
PUT    /api/branches/:id       - Update branch
DELETE /api/branches/:id       - Deactivate branch
```

#### 2. **Roles API** (`roles` table)
```
GET    /api/roles              - List all roles
```

#### 3. **Categories API** (`categories` table)
```
GET    /api/categories         - List all categories
POST   /api/categories         - Create category
PUT    /api/categories/:id     - Update category
```

### **Phase 2: User Management APIs**

#### 4. **Users API** (`users` table)
```
POST   /api/auth/login         - User authentication
POST   /api/auth/logout        - User logout
GET    /api/users              - List users
GET    /api/users/:id          - Get user details
POST   /api/users              - Create user
PUT    /api/users/:id          - Update user
DELETE /api/users/:id          - Deactivate user
PUT    /api/users/:id/password - Change password
```

### **Phase 3: Item Management APIs**

#### 5. **Items API** (`items` table)
```
GET    /api/items              - List all items
GET    /api/items/:id          - Get item details
GET    /api/items/search?q=    - Search items
POST   /api/items              - Create item
PUT    /api/items/:id          - Update item
DELETE /api/items/:id          - Deactivate item
```

### **Phase 4: Inventory Management APIs** ⚡ **CORE FUNCTIONALITY**

#### 6. **Inventory API** (`inventory`, `stock_movements` tables)
```
GET    /api/inventory/branch/:branchId     - Get branch inventory
GET    /api/inventory/item/:itemId         - Get item stock across branches
POST   /api/inventory/adjust               - Manual stock adjustment
GET    /api/inventory/low-stock/:branchId  - Get low stock alerts
GET    /api/inventory/movements            - Stock movement history
GET    /api/inventory/movements/item/:id   - Item movement history
```

### **Phase 5: Transfer System APIs** 🎯 **MAIN BUSINESS LOGIC**

#### 7. **Transfer Requests API** (`transfer_requests`, `transfer_request_items` tables)
```
GET    /api/transfers                    - List transfer requests
GET    /api/transfers/:id                - Get transfer details
POST   /api/transfers                    - Create transfer request
PUT    /api/transfers/:id/approve        - Approve transfer
PUT    /api/transfers/:id/reject         - Reject transfer
DELETE /api/transfers/:id                - Cancel transfer
GET    /api/transfers/pending/:branchId  - Pending approvals
```

#### 8. **Dispatch API** (`dispatch_slips` table)
```
GET    /api/dispatches                   - List dispatches
POST   /api/dispatches                   - Create dispatch slip
GET    /api/dispatches/:id               - Get dispatch details
```

#### 9. **Receiving API** (`receiving_slips`, `receiving_slip_items` tables)
```
GET    /api/receiving                    - List receiving slips
POST   /api/receiving                    - Create receiving slip
GET    /api/receiving/:id                - Get receiving details
POST   /api/receiving/:id/photo          - Upload photo
```

### **Phase 6: Reporting & Dashboard APIs**

#### 10. **Dashboard API** (Multiple tables)
```
GET    /api/dashboard/:branchId          - Branch dashboard data
GET    /api/dashboard/alerts/:branchId   - Alerts and notifications
```

#### 11. **Reports API** (Multiple tables)
```
GET    /api/reports/stock-summary        - Stock summary report
GET    /api/reports/transfer-summary     - Transfer summary report
GET    /api/reports/user-activity        - User activity report
```

---

## 📊 **Tables Used in Each API Endpoint**

### **Single Table APIs**
- **Branches API**: `branches`
- **Roles API**: `roles` 
- **Categories API**: `categories`

### **Two Table APIs**
- **Users API**: `users` + `branches` + `roles`
- **Items API**: `items` + `categories`

### **Multi-Table APIs (Complex)**

#### **Inventory API uses:**
- `inventory` (main)
- `items` (for item details)
- `branches` (for branch info)
- `users` (for who updated)
- `stock_movements` (for history)

#### **Transfer Requests API uses:**
- `transfer_requests` (main)
- `transfer_request_items` (items in request)
- `branches` (from/to branches)
- `users` (requested by, approved by)
- `items` (item details)
- `inventory` (stock availability)

#### **Dispatch API uses:**
- `dispatch_slips` (main)
- `transfer_requests` (transfer info)
- `branches` (branch details)
- `users` (dispatcher info)

#### **Receiving API uses:**
- `receiving_slips` (main)
- `receiving_slip_items` (received items)
- `transfer_requests` (transfer info)
- `dispatch_slips` (dispatch info)
- `items` (item details)
- `users` (receiver info)

#### **Dashboard API uses:**
- `inventory` (current stock)
- `transfer_requests` (pending/overdue)
- `items` (low stock items)
- `branches` (branch info)
- `users` (activity info)

---

## 🎯 **Recommended Implementation Strategy**

### **Week 1: Foundation** 
Start with `branches` → `roles` → `categories` → `users`

### **Week 2: Items & Basic Inventory**
Implement `items` → `inventory` (basic CRUD)

### **Week 3: Stock Management**
Add `stock_movements` → inventory adjustments → stock checking

### **Week 4: Transfer System** 
Build `transfer_requests` → approval workflow

### **Week 5: Dispatch & Receiving**
Complete the workflow with `dispatch_slips` → `receiving_slips`

### **Week 6: Reporting & Polish**
Add dashboards, reports, and mobile APIs

---

## 💡 **Key Tips for API Development**

### **1. Start Simple**
Begin with the `branches` table API - it's the simplest with no dependencies.

### **2. Build Incrementally**  
Each phase builds on the previous one. Don't skip phases.

### **3. Test Each Phase**
Fully test each API before moving to the next level.

### **4. Use Transactions**
For operations involving multiple tables (transfers, stock updates), use database transactions.

### **5. Implement Authentication Early**
Add JWT/session-based auth after the users API.

### **6. Add Validation**
Validate all inputs, especially for stock quantities and user permissions.

### **7. Handle Errors Gracefully**
Implement proper error handling and meaningful error messages.

---

## 🔧 **Sample API Implementation Pattern**

```javascript
// Example: Branches API (Start here)
app.get('/api/branches', async (req, res) => {
  try {
    const branches = await db.query(`
      SELECT branch_id, branch_name, branch_code, city, is_active
      FROM branches 
      WHERE is_active = TRUE 
      ORDER BY branch_name
    `);
    res.json(branches);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

This approach ensures you build a solid foundation and gradually add complexity. Start with the `branches` table API and work your way up the dependency chain!