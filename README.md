# StockSense

> Smart Inventory & Warehouse Management System

StockSense is an inventory and warehouse management platform designed to
reduce dependency on spreadsheets, improve stock visibility, and
introduce safer, more accountable inventory operations.

## Problem

Traditional inventory workflows often depend heavily on Excel sheets and
manual updates. This can lead to inconsistent records, manual
stock-entry errors, uncontrolled stock adjustments, lack of
accountability, and stock shortages.

StockSense addresses these problems through centralized inventory
management, validation, role-based approvals, auditability, and smart
reorder suggestions.

## Core Features

### 1. CSV / Excel Import with Validation

StockSense allows inventory data to be imported from CSV/Excel files.

Workflow:

``` text
Upload File
    ↓
Parse Data
    ↓
Validate Records
    ↓
Preview Errors
    ↓
Confirm Import
    ↓
Update Inventory
```

Validation can identify:

-   Missing SKU
-   Duplicate SKU
-   Invalid quantity
-   Negative quantity
-   Invalid unit cost
-   Unknown warehouse
-   Missing product information

### 2. Role-Based Access & Approval Workflow

**Staff** can view inventory, create operational records, and request
stock adjustments with reasons.

**Managers** can approve or reject adjustments and perform authorized
inventory corrections.

Workflow:

``` text
Staff
  ↓
Adjustment Request
  ↓
Reason Required
  ↓
Manager Review
  ↓
Approve / Reject
  ↓
Stock Updated
```

### 3. Audit Trail

Important inventory operations record:

-   Who performed the action
-   What changed
-   Previous value
-   New value
-   Reason
-   Timestamp
-   Related operation/entity

Example:

``` text
10:32 AM
Staff requested stock adjustment
Steel Frame: 100 → 70
Reason: Damaged

10:35 AM
Manager approved adjustment

10:35 AM
Stock updated: 100 → 70
```

### 4. Smart Reorder Suggestions

StockSense identifies products approaching their reorder point and
suggests replenishment.

A simple reorder model can use:

``` text
Average Daily Usage = Total Usage / Number of Days

Reorder Point =
Average Daily Usage × Lead Time + Safety Stock
```

Example:

``` text
Product: Steel Frame
Current Stock: 20
Average Daily Usage: 8
Supplier Lead Time: 5 days
Safety Stock: 10

Reorder Point = 8 × 5 + 10 = 50

Current Stock: 20
Reorder Point: 50

→ Reorder Suggested
```

The suggestion can connect directly to the receipt workflow:

``` text
Low Stock
    ↓
Reorder Suggestion
    ↓
Suggested Quantity
    ↓
Create Receipt
```

### 5. Inventory Safety

StockSense distinguishes physical stock from stock that is actually
available for use.

``` text
Available Stock =
On Hand Stock - Reserved Stock
```

Example:

``` text
On Hand: 100
Reserved: 30
Available: 70
```

A delivery requesting 80 units can be blocked because only 70 units are
available.

## Main Application Areas

-   Dashboard
-   Stock
-   Receipts
-   Delivery
-   Warehouse
-   Locations
-   Move History
-   Inventory Adjustments
-   Approvals
-   Audit Trail
-   Smart Reorder Suggestions

## Key User Flows

### Replenishment

``` text
CSV / Excel Import
        ↓
Inventory Validation
        ↓
Stock Available
        ↓
Stock Usage
        ↓
Low Stock Detection
        ↓
Smart Reorder Suggestion
        ↓
Create Receipt
```

### Stock Adjustment

``` text
Stock Count
    ↓
Adjustment Request
    ↓
Reason Required
    ↓
Manager Approval
    ↓
Stock Updated
    ↓
Audit Trail
```

## Demo Scenario

The primary demo scenario is a warehouse running low on a product.

1.  Import inventory from a spreadsheet.
2.  Validate the uploaded records.
3.  Detect a product below its reorder point.
4.  Generate a reorder suggestion using recent usage, lead time, and
    safety stock.
5.  Create a receipt from the suggestion.
6.  Submit a stock adjustment when a physical count differs from system
    stock.
7.  Have a manager approve or reject the adjustment.
8.  Show the resulting audit trail.

This demonstrates the flow from inventory input to intelligent
replenishment and accountable stock management.

## Problems Addressed

  Problem                          StockSense Solution
  -------------------------------- --------------------------------
  No bulk import                   CSV/Excel import
  No validation                    Import validation and preview
  Same permissions for all users   Role-based access
  Uncontrolled stock adjustments   Approval workflow
  No adjustment reason             Required reason codes
  No accountability                Audit trail
  Negative stock                   Availability checks
  No reservation concept           Reserved vs available stock
  Low-stock alerts only            Smart reorder suggestions
  No inventory value               Unit-cost based valuation
  Limited operational visibility   Dashboard and movement history

## Future Enhancements

-   Barcode and QR scanning
-   Mobile warehouse interface
-   Supplier and customer directories
-   Customer and vendor returns
-   Batch, lot, serial, and expiry tracking
-   Internal stock transfers
-   Email and in-app notifications
-   Inventory valuation reports
-   Fast/slow/dead stock analytics
-   PDF and Excel reporting
-   Demand forecasting
-   Advanced usage prediction

## Suggested Architecture

``` text
Frontend
│
├── Dashboard
├── Stock
├── Receipts
├── Delivery
├── Warehouse
├── Locations
├── Approvals
├── Audit Trail
└── Analytics

Backend
│
├── Authentication
├── Authorization
├── Products
├── Inventory
├── Stock Movements
├── Receipts
├── Deliveries
├── Adjustments
├── Approvals
├── Audit Logs
└── Reorder Engine

Database
│
├── Users
├── Roles
├── Products
├── Warehouses
├── Locations
├── Stock
├── Stock Movements
├── Receipts
├── Deliveries
├── Adjustments
└── Audit Logs
```

## Development Priorities

1.  Authentication and roles
2.  Product and stock data
3.  CSV/Excel import and validation
4.  Stock reservation and safety checks
5.  Adjustment workflow
6.  Manager approval
7.  Audit trail
8.  Smart reorder suggestions
9.  Dashboard integration
10. Analytics and reporting

## Project Goal

StockSense is designed to answer:

-   **What stock do we have?**
-   **What stock is actually available?**
-   **What changed?**
-   **Who changed it?**
-   **Why was it changed?**
-   **Does the change require approval?**
-   **Which products need replenishment?**
-   **How much should we reorder?**

The objective is to move inventory management from a spreadsheet-driven
process toward a centralized, validated, and accountable workflow.

## Status

**Project:** StockSense\
**Stage:** MVP / Hackathon Development\
**Primary Focus:** Inventory management, operational controls, smart
replenishment, and accountability

## Team

Built as part of a collaborative project.

Individual responsibilities may include:

-   Inventory management
-   CSV/Excel import
-   Role-based access
-   Approval workflows
-   Audit logging
-   Smart reorder logic
-   Analytics
