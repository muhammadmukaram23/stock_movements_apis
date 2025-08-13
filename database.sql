-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Aug 12, 2025 at 09:01 AM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `inventory_management_system`
--

DELIMITER $$
--
-- Procedures
--
CREATE DEFINER=`root`@`localhost` PROCEDURE `update_stock` (IN `p_item_id` INT, IN `p_branch_id` INT, IN `p_quantity` INT, IN `p_movement_type` VARCHAR(20), IN `p_reference_type` VARCHAR(20), IN `p_reference_id` INT, IN `p_user_id` INT, IN `p_notes` TEXT)   BEGIN
    DECLARE current_stock_val INT DEFAULT 0;
    DECLARE new_stock_val INT;
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Get current stock (lock the row)
    SELECT COALESCE(current_stock, 0) INTO current_stock_val
    FROM inventory 
    WHERE item_id = p_item_id AND branch_id = p_branch_id
    FOR UPDATE;
    
    -- Calculate new stock based on movement type
    IF p_movement_type IN ('IN', 'TRANSFER_IN', 'ADJUSTMENT_IN') THEN
        SET new_stock_val = current_stock_val + p_quantity;
    ELSEIF p_movement_type IN ('OUT', 'TRANSFER_OUT', 'ADJUSTMENT_OUT') THEN
        SET new_stock_val = current_stock_val - p_quantity;
    ELSEIF p_movement_type = 'ADJUSTMENT' THEN
        -- For adjustment, p_quantity can be positive or negative
        SET new_stock_val = current_stock_val + p_quantity;
    ELSE
        SET new_stock_val = current_stock_val;
    END IF;
    
    -- Ensure stock doesn't go negative (optional business rule)
    IF new_stock_val < 0 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Insufficient stock for this operation';
    END IF;
    
    -- Update or insert inventory record
    INSERT INTO inventory (item_id, branch_id, current_stock, updated_by)
    VALUES (p_item_id, p_branch_id, new_stock_val, p_user_id)
    ON DUPLICATE KEY UPDATE 
        current_stock = new_stock_val,
        updated_by = p_user_id,
        last_updated = CURRENT_TIMESTAMP;
    
    -- Insert stock movement record
    INSERT INTO stock_movements (
        item_id, branch_id, movement_type, quantity, 
        previous_stock, new_stock, reference_type, 
        reference_id, notes, created_by
    ) VALUES (
        p_item_id, p_branch_id, p_movement_type, p_quantity,
        current_stock_val, new_stock_val, p_reference_type,
        p_reference_id, p_notes, p_user_id
    );
    
    COMMIT;
END$$

--
-- Functions
--
CREATE DEFINER=`root`@`localhost` FUNCTION `generate_transfer_number` () RETURNS VARCHAR(50) CHARSET utf8mb4 COLLATE utf8mb4_general_ci DETERMINISTIC READS SQL DATA BEGIN
    DECLARE next_seq INT;
    DECLARE date_string VARCHAR(8);
    
    SET date_string = DATE_FORMAT(NOW(), '%Y%m%d');
    
    SELECT COALESCE(MAX(CAST(SUBSTRING(transfer_number, -4) AS UNSIGNED)), 0) + 1 
    INTO next_seq
    FROM transfer_requests 
    WHERE transfer_number LIKE CONCAT('TR-', date_string, '-%');
    
    RETURN CONCAT('TR-', date_string, '-', LPAD(next_seq, 4, '0'));
END$$

DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `branches`
--

CREATE TABLE `branches` (
  `branch_id` int(11) NOT NULL,
  `branch_name` varchar(100) NOT NULL,
  `branch_code` varchar(10) NOT NULL,
  `city` varchar(50) NOT NULL,
  `address` text DEFAULT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `email` varchar(100) DEFAULT NULL,
  `branch_manager_name` varchar(100) DEFAULT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `branches`
--

INSERT INTO `branches` (`branch_id`, `branch_name`, `branch_code`, `city`, `address`, `phone`, `email`, `branch_manager_name`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'Lahore Head Office', 'LHR001', 'Lahore', 'Plot 15, MM Alam Road, Gulberg III, Lahore, Punjab', '+92-42-35711234', 'lahore@techcorp.pk', 'Ahmed Ali Khan', 1, '2025-08-12 06:30:07', '2025-08-12 06:30:07'),
(2, 'Haripur Distribution Center', 'HRP001', 'Haripur', 'Main GT Road, Near Bypass, Haripur, KPK', '+92-995-612345', 'haripur@techcorp.pk', 'Muhammad Hassan Shah', 1, '2025-08-12 06:30:07', '2025-08-12 06:30:07'),
(3, 'Islamabad Branch', 'ISB001', 'Islamabad', 'Office 301, Blue Area Plaza, Islamabad, ICT', '+92-51-2345678', 'islamabad@techcorp.pk', 'Sarah Ahmed Malik', 1, '2025-08-12 06:30:07', '2025-08-12 06:30:07'),
(4, 'Karachi South Branch', 'KHI001', 'Karachi', 'Suite 12, Clifton Block 9, Main Clifton Road, Karachi, Sindh', '+92-21-35678901', 'karachi@techcorp.pk', 'Tariq Mahmood Qureshi', 1, '2025-08-12 06:30:07', '2025-08-12 06:30:07'),
(5, 'Faisalabad Branch', 'FSD001', 'Faisalabad', 'Shop 45, Kohinoor Plaza, Susan Road, Faisalabad, Punjab', '+92-41-2567890', 'faisalabad@techcorp.pk', 'Fatima Nasir', 1, '2025-08-12 06:30:07', '2025-08-12 06:30:07'),
(6, 'Peshawar Branch', 'PSH001', 'Peshawar', 'Ground Floor, Saddar Road, University Town, Peshawar, KPK', '+92-91-5789012', 'peshawar@techcorp.pk', 'Khan Bahadur', 1, '2025-08-12 06:30:07', '2025-08-12 06:30:07'),
(7, 'Multan Warehouse', 'MLT001', 'Multan', 'Warehouse Complex, Bosan Road, Multan, Punjab', '+92-61-6789123', 'multan@techcorp.pk', 'Asma Khatoon', 1, '2025-08-12 06:30:07', '2025-08-12 06:30:07'),
(8, 'Quetta Branch', 'QTA001', 'Quetta', 'Jinnah Road, Near GPO, Quetta, Balochistan', '+92-81-2890123', 'quetta@techcorp.pk', 'Abdul Rashid', 1, '2025-08-12 06:30:07', '2025-08-12 06:30:07');

-- --------------------------------------------------------

--
-- Table structure for table `categories`
--

CREATE TABLE `categories` (
  `category_id` int(11) NOT NULL,
  `category_name` varchar(100) NOT NULL,
  `category_code` varchar(20) NOT NULL,
  `description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `categories`
--

INSERT INTO `categories` (`category_id`, `category_name`, `category_code`, `description`, `created_at`) VALUES
(1, 'Security Equipment', 'SEC', 'CCTV cameras, access control systems, security hardware', '2025-08-12 06:30:35'),
(2, 'IT Hardware', 'ITH', 'Computers, servers, networking equipment, storage devices', '2025-08-12 06:30:35'),
(3, 'Electronics', 'ELEC', 'Consumer electronics, components, accessories', '2025-08-12 06:30:35'),
(4, 'Office Equipment', 'OFF', 'Printers, scanners, projectors, office machines', '2025-08-12 06:30:35'),
(5, 'Furniture', 'FURN', 'Office furniture, chairs, desks, storage units', '2025-08-12 06:30:35'),
(6, 'Stationery', 'STAT', 'Office supplies, paper, pens, files', '2025-08-12 06:30:35'),
(7, 'Networking', 'NET', 'Routers, switches, cables, wireless equipment', '2025-08-12 06:30:35'),
(8, 'Software', 'SOFT', 'Software licenses, applications, operating systems', '2025-08-12 06:30:35'),
(9, 'Mobile Devices', 'MOB', 'Smartphones, tablets, mobile accessories', '2025-08-12 06:30:35'),
(10, 'Audio Visual', 'AV', 'Speakers, microphones, presentation equipment', '2025-08-12 06:30:35');

-- --------------------------------------------------------

--
-- Table structure for table `dispatch_slips`
--

CREATE TABLE `dispatch_slips` (
  `dispatch_id` int(11) NOT NULL,
  `dispatch_number` varchar(50) NOT NULL,
  `transfer_id` int(11) NOT NULL,
  `dispatched_by` int(11) NOT NULL,
  `loader_name` varchar(100) DEFAULT NULL,
  `vehicle_info` varchar(100) DEFAULT NULL,
  `dispatch_date` timestamp NOT NULL DEFAULT current_timestamp(),
  `expected_delivery_date` date DEFAULT NULL,
  `notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `dispatch_slips`
--

INSERT INTO `dispatch_slips` (`dispatch_id`, `dispatch_number`, `transfer_id`, `dispatched_by`, `loader_name`, `vehicle_info`, `dispatch_date`, `expected_delivery_date`, `notes`) VALUES
(1, 'DS-20241211-0001', 1, 5, 'Rashid Ali', 'Truck LES-1234, Driver: Akram Khan', '2024-12-11 03:00:00', '2024-12-12', 'Handle cameras carefully'),
(2, 'DS-20241209-0001', 2, 5, 'Imran Shah', 'Van LHR-5678, Driver: Sajid Hussain', '2024-12-09 11:30:00', '2024-12-10', 'Laptops in secure packaging'),
(3, 'DS-20241206-0001', 3, 5, 'Ahmad Raza', 'Truck KHI-9012, Driver: Tariq Mehmood', '2024-12-06 12:00:00', '2024-12-08', 'Furniture items - handle with care'),
(4, 'DS-20241213-0001', 4, 5, 'Sohail Ahmed', 'Van HRP-3456, Driver: Nasir Ali', '2024-12-13 03:15:00', '2024-12-13', 'Office equipment delivery'),
(5, 'DS-20241212-0001', 5, 5, 'Fahad Malik', 'Truck FSD-7890, Driver: Waqar Ahmed', '2024-12-12 09:45:00', '2024-12-13', 'IT hardware - fragile items');

-- --------------------------------------------------------

--
-- Table structure for table `inventory`
--

CREATE TABLE `inventory` (
  `inventory_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `branch_id` int(11) NOT NULL,
  `current_stock` int(11) NOT NULL DEFAULT 0,
  `reserved_stock` int(11) NOT NULL DEFAULT 0,
  `available_stock` int(11) GENERATED ALWAYS AS (`current_stock` - `reserved_stock`) STORED,
  `last_updated` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp(),
  `updated_by` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `inventory`
--

INSERT INTO `inventory` (`inventory_id`, `item_id`, `branch_id`, `current_stock`, `reserved_stock`, `last_updated`, `updated_by`) VALUES
(171, 1, 1, 45, 0, '2025-08-12 06:35:22', 2),
(172, 2, 1, 12, 0, '2025-08-12 06:35:22', 2),
(173, 3, 1, 25, 0, '2025-08-12 06:35:22', 2),
(174, 4, 1, 18, 0, '2025-08-12 06:35:22', 2),
(175, 5, 1, 35, 2, '2025-08-12 06:35:22', 2),
(176, 6, 1, 28, 3, '2025-08-12 06:38:33', 2),
(177, 7, 1, 8, 0, '2025-08-12 06:35:22', 2),
(178, 8, 1, 65, 10, '2025-08-12 06:38:33', 2),
(179, 9, 1, 85, 5, '2025-08-12 06:35:22', 2),
(180, 10, 1, 15, 0, '2025-08-12 06:35:22', 2),
(181, 11, 1, 42, 0, '2025-08-12 06:35:22', 2),
(182, 12, 1, 22, 0, '2025-08-12 06:35:22', 2),
(183, 13, 1, 38, 0, '2025-08-12 06:35:22', 2),
(184, 14, 1, 28, 0, '2025-08-12 06:35:22', 2),
(185, 15, 1, 18, 0, '2025-08-12 06:35:22', 2),
(186, 16, 1, 285, 10, '2025-08-12 06:35:22', 2),
(187, 17, 1, 85, 0, '2025-08-12 06:35:22', 2),
(188, 18, 1, 125, 0, '2025-08-12 06:35:22', 2),
(189, 19, 1, 32, 0, '2025-08-12 06:35:22', 2),
(190, 20, 1, 15, 0, '2025-08-12 06:35:22', 2),
(191, 21, 1, 35, 0, '2025-08-12 06:35:22', 2),
(192, 22, 1, 45, 2, '2025-08-12 06:35:22', 2),
(193, 23, 1, 25, 0, '2025-08-12 06:35:22', 2),
(194, 24, 1, 85, 0, '2025-08-12 06:35:22', 2),
(195, 25, 1, 12, 0, '2025-08-12 06:35:22', 2),
(196, 1, 2, 18, 0, '2025-08-12 06:38:33', 6),
(197, 2, 2, 3, 0, '2025-08-12 06:35:22', 6),
(198, 3, 2, 5, 0, '2025-08-12 06:35:22', 6),
(199, 4, 2, 4, 0, '2025-08-12 06:35:22', 6),
(200, 5, 2, 12, 0, '2025-08-12 06:35:22', 6),
(201, 6, 2, 8, 0, '2025-08-12 06:35:22', 6),
(202, 7, 2, 2, 0, '2025-08-12 06:35:22', 6),
(203, 8, 2, 15, 0, '2025-08-12 06:35:22', 6),
(204, 9, 2, 25, 0, '2025-08-12 06:35:22', 6),
(205, 10, 2, 6, 0, '2025-08-12 06:35:22', 6),
(206, 11, 2, 8, 0, '2025-08-12 06:35:22', 6),
(207, 16, 2, 45, 0, '2025-08-12 06:35:22', 6),
(208, 17, 2, 15, 0, '2025-08-12 06:35:22', 6),
(209, 18, 2, 25, 0, '2025-08-12 06:35:22', 6),
(210, 22, 2, 12, 0, '2025-08-12 06:35:22', 6),
(211, 23, 2, 8, 0, '2025-08-12 06:35:22', 6),
(212, 1, 3, 15, 0, '2025-08-12 06:35:22', 9),
(213, 2, 3, 5, 0, '2025-08-12 06:35:22', 9),
(214, 5, 3, 18, 0, '2025-08-12 06:35:22', 9),
(215, 6, 3, 12, 0, '2025-08-12 06:35:22', 9),
(216, 10, 3, 8, 0, '2025-08-12 06:35:22', 9),
(217, 11, 3, 15, 0, '2025-08-12 06:35:22', 9),
(218, 16, 3, 85, 0, '2025-08-12 06:35:22', 9),
(219, 19, 3, 15, 0, '2025-08-12 06:35:22', 9),
(220, 22, 3, 20, 0, '2025-08-12 06:35:22', 9),
(221, 25, 3, 6, 0, '2025-08-12 06:35:22', 9),
(222, 1, 4, 22, 0, '2025-08-12 06:35:22', 11),
(223, 5, 4, 15, 0, '2025-08-12 06:35:22', 11),
(224, 6, 4, 18, 0, '2025-08-12 06:35:22', 11),
(225, 10, 4, 12, 0, '2025-08-12 06:35:22', 11),
(226, 16, 4, 125, 0, '2025-08-12 06:35:22', 11),
(227, 19, 4, 25, 0, '2025-08-12 06:35:22', 11),
(228, 22, 4, 28, 0, '2025-08-12 06:35:22', 11),
(229, 23, 4, 15, 0, '2025-08-12 06:35:22', 11),
(230, 1, 5, 12, 0, '2025-08-12 06:35:22', 13),
(231, 6, 5, 8, 0, '2025-08-12 06:35:22', 13),
(232, 10, 5, 5, 0, '2025-08-12 06:35:22', 13),
(233, 16, 5, 65, 0, '2025-08-12 06:35:22', 13),
(234, 22, 5, 15, 0, '2025-08-12 06:35:22', 13),
(235, 23, 5, 8, 0, '2025-08-12 06:35:22', 13);

-- --------------------------------------------------------

--
-- Table structure for table `items`
--

CREATE TABLE `items` (
  `item_id` int(11) NOT NULL,
  `item_name` varchar(200) NOT NULL,
  `item_code` varchar(50) NOT NULL,
  `category_id` int(11) NOT NULL,
  `description` text DEFAULT NULL,
  `unit_of_measure` varchar(20) DEFAULT 'PCS',
  `minimum_stock_level` int(11) DEFAULT 0,
  `maximum_stock_level` int(11) DEFAULT 1000,
  `unit_price` decimal(10,2) DEFAULT 0.00,
  `is_active` tinyint(1) DEFAULT 1,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `items`
--

INSERT INTO `items` (`item_id`, `item_name`, `item_code`, `category_id`, `description`, `unit_of_measure`, `minimum_stock_level`, `maximum_stock_level`, `unit_price`, `is_active`, `created_at`, `updated_at`) VALUES
(1, 'Hikvision HD Camera DS-2CE16', 'CAM001', 1, '2MP HD CCTV Camera with Night Vision', 'PCS', 10, 100, 12500.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(2, 'Dahua NVR 16 Channel', 'NVR001', 1, '16 Channel Network Video Recorder', 'PCS', 5, 50, 45000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(3, 'Access Control Card Reader', 'ACR001', 1, 'RFID Card Reader for Door Access', 'PCS', 8, 80, 8500.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(4, 'CCTV Monitor 22 Inch', 'MON001', 1, '22 Inch LCD Monitor for Security', 'PCS', 6, 60, 18000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(5, 'Dell OptiPlex 3080 Desktop', 'DES001', 2, 'Intel i5, 8GB RAM, 256GB SSD', 'PCS', 5, 50, 95000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(6, 'HP ProBook 450 Laptop', 'LAP001', 2, 'Intel i7, 16GB RAM, 512GB SSD', 'PCS', 8, 80, 125000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(7, 'Dell PowerEdge R740 Server', 'SRV001', 2, 'Dual Xeon, 32GB RAM, 2TB HDD', 'PCS', 2, 20, 450000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(8, 'Seagate External HDD 2TB', 'HDD001', 2, '2TB External Hard Drive USB 3.0', 'PCS', 15, 150, 8500.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(9, 'Kingston RAM 8GB DDR4', 'RAM001', 2, '8GB DDR4 2666MHz Memory Module', 'PCS', 25, 250, 6500.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(10, 'Samsung LED TV 43 Inch', 'TV001', 3, '43 Inch Full HD LED Television', 'PCS', 3, 30, 65000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(11, 'Canon PIXMA Printer', 'PRT001', 4, 'All-in-One Inkjet Printer', 'PCS', 10, 100, 22000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(12, 'Epson Scanner V600', 'SCN001', 4, 'Photo and Document Scanner', 'PCS', 5, 50, 35000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(13, 'Executive Office Chair', 'CHR001', 5, 'Ergonomic Executive Chair with Leather', 'PCS', 8, 80, 28000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(14, 'Office Desk 4x2 Feet', 'DSK001', 5, 'Wooden Office Desk with Drawers', 'PCS', 5, 50, 35000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(15, 'Filing Cabinet 4 Drawer', 'CAB001', 5, 'Steel Filing Cabinet with Lock', 'PCS', 6, 60, 15000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(16, 'A4 Paper Ream 80GSM', 'PPR001', 6, 'A4 Size Paper 500 Sheets per Ream', 'REAM', 50, 500, 850.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(17, 'Ballpoint Pen Blue', 'PEN001', 6, 'Blue Ballpoint Pen', 'BOX', 20, 200, 450.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(18, 'Ring File A4 Size', 'FILE001', 6, 'A4 Ring File with Index', 'PCS', 30, 300, 125.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(19, 'TP-Link Router AC1750', 'RTR001', 7, 'Dual Band Wireless Router', 'PCS', 12, 120, 8500.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(20, 'Cisco Switch 24 Port', 'SWT001', 7, '24 Port Managed Switch', 'PCS', 4, 40, 85000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(21, 'CAT6 Cable 305M', 'CBL001', 7, 'Category 6 Network Cable Roll', 'ROLL', 8, 80, 12000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(22, 'Samsung Galaxy A54', 'PHN001', 9, 'Android Smartphone 128GB', 'PCS', 15, 150, 68000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(23, 'iPad Air 64GB', 'TAB001', 9, 'Apple iPad Air WiFi Model', 'PCS', 6, 60, 95000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(24, 'Mobile Power Bank 10000mAh', 'PWR001', 9, 'Portable Charger with USB-C', 'PCS', 20, 200, 3500.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(25, 'JBL Professional Speaker', 'SPK001', 10, 'Bluetooth Speaker for Presentations', 'PCS', 8, 80, 15000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(26, 'Wireless Microphone', 'MIC001', 10, 'Professional Wireless Microphone', 'PCS', 6, 60, 12500.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35'),
(27, 'Projector Benq MX550', 'PRJ001', 10, '3600 Lumens XGA Projector', 'PCS', 3, 30, 75000.00, 1, '2025-08-12 06:30:35', '2025-08-12 06:30:35');

-- --------------------------------------------------------

--
-- Table structure for table `receiving_slips`
--

CREATE TABLE `receiving_slips` (
  `receiving_id` int(11) NOT NULL,
  `receiving_number` varchar(50) NOT NULL,
  `transfer_id` int(11) NOT NULL,
  `dispatch_id` int(11) NOT NULL,
  `received_by` int(11) NOT NULL,
  `receiving_date` timestamp NOT NULL DEFAULT current_timestamp(),
  `condition_on_arrival` enum('GOOD','DAMAGED','PARTIAL') DEFAULT 'GOOD',
  `notes` text DEFAULT NULL,
  `photo_path` varchar(255) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `receiving_slips`
--

INSERT INTO `receiving_slips` (`receiving_id`, `receiving_number`, `transfer_id`, `dispatch_id`, `received_by`, `receiving_date`, `condition_on_arrival`, `notes`, `photo_path`) VALUES
(1, 'RS-20241212-0001', 1, 1, 8, '2024-12-12 10:30:00', 'GOOD', 'All cameras received in perfect condition', '/uploads/receiving/RS-20241212-0001.jpg'),
(2, 'RS-20241210-0001', 2, 2, 10, '2024-12-10 06:20:00', 'GOOD', 'Laptops and supplies received successfully', '/uploads/receiving/RS-20241210-0001.jpg'),
(3, 'RS-20241208-0001', 3, 3, 12, '2024-12-08 04:45:00', 'PARTIAL', 'One chair had minor scratch, rest items good', '/uploads/receiving/RS-20241208-0001.jpg');

-- --------------------------------------------------------

--
-- Table structure for table `receiving_slip_items`
--

CREATE TABLE `receiving_slip_items` (
  `receiving_item_id` int(11) NOT NULL,
  `receiving_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `dispatched_quantity` int(11) NOT NULL,
  `received_quantity` int(11) NOT NULL,
  `damaged_quantity` int(11) DEFAULT 0,
  `condition_notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `receiving_slip_items`
--

INSERT INTO `receiving_slip_items` (`receiving_item_id`, `receiving_id`, `item_id`, `dispatched_quantity`, `received_quantity`, `damaged_quantity`, `condition_notes`) VALUES
(1, 1, 1, 10, 10, 0, 'All cameras in excellent condition'),
(2, 1, 3, 5, 5, 0, 'Card readers working properly'),
(3, 1, 4, 3, 3, 0, 'Monitors tested and functional'),
(4, 2, 6, 5, 5, 0, 'Laptops sealed and undamaged'),
(5, 2, 16, 50, 50, 0, 'Paper reams in good condition'),
(6, 2, 19, 8, 8, 0, 'Routers with all accessories'),
(7, 3, 13, 6, 5, 1, 'One chair has minor scratch on armrest'),
(8, 3, 14, 4, 4, 0, 'Desks assembled and ready to use'),
(9, 3, 17, 25, 25, 0, 'Pen boxes intact');

-- --------------------------------------------------------

--
-- Table structure for table `roles`
--

CREATE TABLE `roles` (
  `role_id` int(11) NOT NULL,
  `role_name` varchar(50) NOT NULL,
  `role_description` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `roles`
--

INSERT INTO `roles` (`role_id`, `role_name`, `role_description`, `created_at`) VALUES
(1, 'Super Admin', 'System administrator with complete access to all modules', '2025-08-12 06:30:35'),
(2, 'Branch Manager', 'Branch manager with full branch-level access and approval rights', '2025-08-12 06:30:35'),
(3, 'Warehouse Manager', 'Warehouse operations manager with inventory control', '2025-08-12 06:30:35'),
(4, 'Inventory Clerk', 'Staff responsible for daily inventory operations', '2025-08-12 06:30:35'),
(5, 'Store Keeper', 'Basic inventory handling and record keeping', '2025-08-12 06:30:35'),
(6, 'Dispatch Officer', 'Handles outgoing shipments and dispatch operations', '2025-08-12 06:30:35'),
(7, 'Receiving Officer', 'Manages incoming inventory and receiving operations', '2025-08-12 06:30:35'),
(8, 'Auditor', 'Read-only access for audit and compliance purposes', '2025-08-12 06:30:35'),
(9, 'Data Entry Operator', 'Basic data entry with limited access', '2025-08-12 06:30:35'),
(10, 'Viewer', 'Read-only access to inventory reports', '2025-08-12 06:30:35');

-- --------------------------------------------------------

--
-- Table structure for table `stock_discrepancies`
--

CREATE TABLE `stock_discrepancies` (
  `discrepancy_id` int(11) NOT NULL,
  `branch_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `expected_stock` int(11) NOT NULL,
  `actual_stock` int(11) NOT NULL,
  `difference` int(11) NOT NULL,
  `discrepancy_type` enum('SHORTAGE','EXCESS') NOT NULL,
  `reported_by` int(11) NOT NULL,
  `investigation_notes` text DEFAULT NULL,
  `resolution_notes` text DEFAULT NULL,
  `status` enum('REPORTED','INVESTIGATING','RESOLVED') DEFAULT 'REPORTED',
  `reported_date` timestamp NOT NULL DEFAULT current_timestamp(),
  `resolved_date` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `stock_discrepancies`
--

INSERT INTO `stock_discrepancies` (`discrepancy_id`, `branch_id`, `item_id`, `expected_stock`, `actual_stock`, `difference`, `discrepancy_type`, `reported_by`, `investigation_notes`, `resolution_notes`, `status`, `reported_date`, `resolved_date`) VALUES
(1, 1, 16, 290, 285, 5, 'SHORTAGE', 4, 'Physical count shows 5 reams missing', 'Found damaged reams in storage, adjusted inventory', 'RESOLVED', '2024-12-05 09:00:00', '2024-12-05 11:30:00'),
(2, 2, 1, 15, 18, 3, 'EXCESS', 7, 'More cameras found than recorded', 'Transfer not properly recorded in system', 'RESOLVED', '2024-12-10 04:15:00', '2024-12-10 06:20:00'),
(3, 3, 9, 20, 25, 5, 'EXCESS', 10, 'Extra RAM modules discovered', 'Previous transfer quantities incorrectly entered', 'INVESTIGATING', '2024-12-12 10:30:00', NULL),
(4, 4, 13, 6, 5, 1, 'SHORTAGE', 12, 'One executive chair missing', 'Chair damaged during receiving, investigating disposal records', 'RESOLVED', '2024-12-08 03:45:00', '2024-12-08 09:20:00');

-- --------------------------------------------------------

--
-- Table structure for table `stock_movements`
--

CREATE TABLE `stock_movements` (
  `movement_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `branch_id` int(11) NOT NULL,
  `movement_type` enum('IN','OUT','ADJUSTMENT','TRANSFER_OUT','TRANSFER_IN') NOT NULL,
  `quantity` int(11) NOT NULL,
  `previous_stock` int(11) NOT NULL,
  `new_stock` int(11) NOT NULL,
  `reference_type` enum('PURCHASE','SALE','TRANSFER','ADJUSTMENT','INITIAL') NOT NULL,
  `reference_id` int(11) DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `created_by` int(11) NOT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `stock_movements`
--

INSERT INTO `stock_movements` (`movement_id`, `item_id`, `branch_id`, `movement_type`, `quantity`, `previous_stock`, `new_stock`, `reference_type`, `reference_id`, `notes`, `created_by`, `created_at`) VALUES
(1, 1, 1, 'IN', 50, 0, 50, 'INITIAL', NULL, 'Initial inventory load', 2, '2024-11-15 04:00:00'),
(2, 1, 2, 'IN', 20, 0, 20, 'INITIAL', NULL, 'Initial inventory load', 6, '2024-11-15 05:00:00'),
(3, 6, 1, 'IN', 30, 0, 30, 'INITIAL', NULL, 'Initial laptop inventory', 2, '2024-11-15 04:30:00'),
(4, 1, 1, 'TRANSFER_OUT', 10, 55, 45, 'TRANSFER', 1, 'Transferred to Haripur', 5, '2024-12-11 03:00:00'),
(5, 1, 2, 'TRANSFER_IN', 10, 8, 18, 'TRANSFER', 1, 'Received from Lahore', 8, '2024-12-12 10:30:00'),
(6, 3, 1, 'TRANSFER_OUT', 5, 30, 25, 'TRANSFER', 1, 'Transferred to Haripur', 5, '2024-12-11 03:00:00'),
(7, 3, 2, 'TRANSFER_IN', 5, 0, 5, 'TRANSFER', 1, 'Received from Lahore', 8, '2024-12-12 10:30:00'),
(8, 6, 1, 'TRANSFER_OUT', 5, 33, 28, 'TRANSFER', 2, 'Transferred to Islamabad', 5, '2024-12-09 11:30:00'),
(9, 6, 3, 'TRANSFER_IN', 5, 7, 12, 'TRANSFER', 2, 'Received from Lahore', 10, '2024-12-10 06:20:00'),
(10, 16, 1, 'ADJUSTMENT', -5, 290, 285, 'ADJUSTMENT', NULL, 'Physical count adjustment', 4, '2024-12-05 09:30:00'),
(11, 9, 1, 'ADJUSTMENT', 5, 80, 85, 'ADJUSTMENT', NULL, 'Found missing RAM modules', 4, '2024-12-08 06:15:00'),
(12, 1, 1, 'IN', 5, 45, 50, 'PURCHASE', NULL, 'New camera purchase', 2, '2024-12-07 11:00:00'),
(13, 22, 1, 'IN', 20, 25, 45, 'PURCHASE', NULL, 'Samsung phones received', 2, '2024-12-06 07:30:00'),
(14, 13, 4, 'OUT', 1, 6, 5, 'ADJUSTMENT', NULL, 'Chair damaged during handling', 12, '2024-12-08 05:45:00');

-- --------------------------------------------------------

--
-- Table structure for table `system_logs`
--

CREATE TABLE `system_logs` (
  `log_id` int(11) NOT NULL,
  `user_id` int(11) DEFAULT NULL,
  `action` varchar(100) NOT NULL,
  `table_affected` varchar(50) DEFAULT NULL,
  `record_id` int(11) DEFAULT NULL,
  `old_values` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`old_values`)),
  `new_values` longtext CHARACTER SET utf8mb4 COLLATE utf8mb4_bin DEFAULT NULL CHECK (json_valid(`new_values`)),
  `ip_address` varchar(45) DEFAULT NULL,
  `user_agent` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `system_logs`
--

INSERT INTO `system_logs` (`log_id`, `user_id`, `action`, `table_affected`, `record_id`, `old_values`, `new_values`, `ip_address`, `user_agent`, `created_at`) VALUES
(1, 1, 'LOGIN', 'users', 1, NULL, '{\"login_time\": \"2024-12-13 08:00:00\"}', '192.168.1.100', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '2024-12-13 03:00:00'),
(2, 2, 'APPROVE_TRANSFER', 'transfer_requests', 9, '{\"status\": \"PENDING\"}', '{\"status\": \"APPROVED\", \"approved_by\": 2}', '192.168.1.105', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '2024-12-13 09:15:00'),
(3, 5, 'CREATE_DISPATCH', 'dispatch_slips', 4, NULL, '{\"transfer_id\": 4, \"dispatched_by\": 5}', '192.168.1.110', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '2024-12-13 03:15:00'),
(4, 8, 'RECEIVE_ITEMS', 'receiving_slips', 1, NULL, '{\"transfer_id\": 1, \"received_by\": 8}', '192.168.2.50', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '2024-12-12 10:30:00'),
(5, 4, 'STOCK_ADJUSTMENT', 'inventory', 16, '{\"current_stock\": 290}', '{\"current_stock\": 285}', '192.168.1.108', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '2024-12-05 09:30:00'),
(6, 6, 'CREATE_TRANSFER', 'transfer_requests', 6, NULL, '{\"from_branch_id\": 1, \"to_branch_id\": 2}', '192.168.2.45', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '2024-12-13 04:15:00'),
(7, 2, 'REJECT_TRANSFER', 'transfer_requests', 10, '{\"status\": \"PENDING\"}', '{\"status\": \"REJECTED\", \"approved_by\": 2}', '192.168.1.105', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)', '2024-12-10 04:20:00');

-- --------------------------------------------------------

--
-- Table structure for table `transfer_requests`
--

CREATE TABLE `transfer_requests` (
  `transfer_id` int(11) NOT NULL,
  `transfer_number` varchar(50) NOT NULL,
  `from_branch_id` int(11) NOT NULL,
  `to_branch_id` int(11) NOT NULL,
  `requested_by` int(11) NOT NULL,
  `approved_by` int(11) DEFAULT NULL,
  `status` enum('PENDING','APPROVED','REJECTED','IN_TRANSIT','DELIVERED','CANCELLED') DEFAULT 'PENDING',
  `priority` enum('LOW','MEDIUM','HIGH','URGENT') DEFAULT 'MEDIUM',
  `request_date` timestamp NOT NULL DEFAULT current_timestamp(),
  `approval_date` timestamp NULL DEFAULT NULL,
  `dispatch_date` timestamp NULL DEFAULT NULL,
  `delivery_date` timestamp NULL DEFAULT NULL,
  `notes` text DEFAULT NULL,
  `rejection_reason` text DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `transfer_requests`
--

INSERT INTO `transfer_requests` (`transfer_id`, `transfer_number`, `from_branch_id`, `to_branch_id`, `requested_by`, `approved_by`, `status`, `priority`, `request_date`, `approval_date`, `dispatch_date`, `delivery_date`, `notes`, `rejection_reason`, `created_at`, `updated_at`) VALUES
(1, 'TR-20241210-0001', 1, 2, 6, 2, 'DELIVERED', 'HIGH', '2024-12-10 04:30:00', '2024-12-10 09:20:00', '2024-12-11 03:00:00', '2024-12-12 10:30:00', 'Urgent requirement for security cameras', NULL, '2025-08-12 06:35:41', '2025-08-12 06:35:41'),
(2, 'TR-20241208-0001', 1, 3, 9, 2, 'DELIVERED', 'MEDIUM', '2024-12-08 06:15:00', '2024-12-09 04:45:00', '2024-12-09 11:30:00', '2024-12-10 06:20:00', 'Monthly stock replenishment', NULL, '2025-08-12 06:35:41', '2025-08-12 06:35:41'),
(3, 'TR-20241205-0001', 1, 4, 11, 2, 'DELIVERED', 'LOW', '2024-12-05 09:22:00', '2024-12-06 05:15:00', '2024-12-06 12:00:00', '2024-12-08 04:45:00', 'Regular inventory transfer', NULL, '2025-08-12 06:35:41', '2025-08-12 06:35:41'),
(4, 'TR-20241212-0001', 1, 2, 6, 2, 'IN_TRANSIT', 'MEDIUM', '2024-12-12 05:45:00', '2024-12-12 10:30:00', '2024-12-13 03:15:00', NULL, 'Office equipment for new setup', NULL, '2025-08-12 06:35:41', '2025-08-12 06:35:41'),
(5, 'TR-20241211-0001', 1, 5, 13, 2, 'IN_TRANSIT', 'HIGH', '2024-12-11 11:20:00', '2024-12-12 03:30:00', '2024-12-12 09:45:00', NULL, 'Critical IT hardware needed', NULL, '2025-08-12 06:35:41', '2025-08-12 06:35:41'),
(6, 'TR-20241213-0001', 1, 2, 6, NULL, 'PENDING', 'HIGH', '2024-12-13 04:15:00', NULL, NULL, NULL, 'Additional cameras for expansion', NULL, '2025-08-12 06:35:41', '2025-08-12 06:35:41'),
(7, 'TR-20241213-0002', 1, 3, 9, NULL, 'PENDING', 'MEDIUM', '2024-12-13 06:30:00', NULL, NULL, NULL, 'Stationery supplies running low', NULL, '2025-08-12 06:35:41', '2025-08-12 06:35:41'),
(8, 'TR-20241212-0002', 1, 4, 11, NULL, 'PENDING', 'LOW', '2024-12-12 10:45:00', NULL, NULL, NULL, 'Routine monthly transfer', NULL, '2025-08-12 06:35:41', '2025-08-12 06:35:41'),
(9, 'TR-20241213-0003', 1, 2, 6, 2, 'APPROVED', 'MEDIUM', '2024-12-13 03:20:00', '2024-12-13 09:15:00', NULL, NULL, 'Laptop replacement needed', NULL, '2025-08-12 06:35:41', '2025-08-12 06:35:41'),
(10, 'TR-20241209-0001', 1, 2, 6, 2, 'REJECTED', 'LOW', '2024-12-09 08:10:00', '2024-12-10 04:20:00', NULL, NULL, 'Non-essential items request', 'Items not in stock at source branch', '2025-08-12 06:35:41', '2025-08-12 06:35:41');

-- --------------------------------------------------------

--
-- Table structure for table `transfer_request_items`
--

CREATE TABLE `transfer_request_items` (
  `request_item_id` int(11) NOT NULL,
  `transfer_id` int(11) NOT NULL,
  `item_id` int(11) NOT NULL,
  `requested_quantity` int(11) NOT NULL,
  `approved_quantity` int(11) DEFAULT 0,
  `dispatched_quantity` int(11) DEFAULT 0,
  `received_quantity` int(11) DEFAULT 0,
  `notes` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `transfer_request_items`
--

INSERT INTO `transfer_request_items` (`request_item_id`, `transfer_id`, `item_id`, `requested_quantity`, `approved_quantity`, `dispatched_quantity`, `received_quantity`, `notes`) VALUES
(28, 1, 1, 10, 10, 10, 10, 'HD Cameras for main entrance'),
(29, 1, 3, 5, 5, 5, 5, 'Card readers for office doors'),
(30, 1, 4, 3, 3, 3, 3, 'Monitors for security room'),
(31, 2, 6, 5, 5, 5, 5, 'Laptops for new employees'),
(32, 2, 16, 50, 50, 50, 50, 'Paper for office use'),
(33, 2, 19, 8, 8, 8, 8, 'Routers for network upgrade'),
(34, 3, 13, 6, 6, 6, 6, 'Executive chairs for management'),
(35, 3, 14, 4, 4, 4, 4, 'Desks for new office space'),
(36, 3, 17, 25, 25, 25, 25, 'Pens for daily use'),
(37, 4, 11, 8, 8, 8, 0, 'Printers for branch office'),
(38, 4, 12, 3, 3, 3, 0, 'Scanners for document processing'),
(39, 4, 15, 4, 4, 4, 0, 'Filing cabinets for storage'),
(40, 5, 5, 6, 6, 6, 0, 'Desktop computers urgently needed'),
(41, 5, 9, 15, 15, 15, 0, 'RAM modules for upgrades'),
(42, 5, 20, 2, 2, 2, 0, 'Network switches for office'),
(43, 6, 1, 15, 0, 0, 0, 'Additional security cameras'),
(44, 6, 2, 2, 0, 0, 0, 'NVR systems for recording'),
(45, 7, 16, 100, 0, 0, 0, 'A4 paper for monthly use'),
(46, 7, 17, 50, 0, 0, 0, 'Ballpoint pens'),
(47, 7, 18, 30, 0, 0, 0, 'Ring files for documentation'),
(48, 8, 22, 10, 0, 0, 0, 'Smartphones for field staff'),
(49, 8, 25, 4, 0, 0, 0, 'Power banks for mobile devices'),
(50, 8, 25, 6, 0, 0, 0, 'Speakers for presentation room'),
(51, 9, 6, 3, 3, 0, 0, 'Replacement laptops for damaged units'),
(52, 9, 8, 10, 10, 0, 0, 'External HDDs for backup'),
(53, 10, 24, 2, 0, 0, 0, 'iPads for management'),
(54, 10, 25, 1, 0, 0, 0, 'Projector for meeting room');

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `user_id` int(11) NOT NULL,
  `username` varchar(50) NOT NULL,
  `email` varchar(100) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `full_name` varchar(100) NOT NULL,
  `phone` varchar(20) DEFAULT NULL,
  `branch_id` int(11) NOT NULL,
  `role_id` int(11) NOT NULL,
  `is_active` tinyint(1) DEFAULT 1,
  `last_login` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` timestamp NOT NULL DEFAULT current_timestamp() ON UPDATE current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `users`
--

INSERT INTO `users` (`user_id`, `username`, `email`, `password_hash`, `full_name`, `phone`, `branch_id`, `role_id`, `is_active`, `last_login`, `created_at`, `updated_at`) VALUES
(1, 'superadmin', 'admin@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Muhammad Tariq Chaudhry', '+92-300-1234567', 1, 1, 1, '2025-08-12 06:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(2, 'ahmed.khan', 'ahmed.khan@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Ahmed Ali Khan', '+92-321-2345678', 1, 2, 1, '2025-08-12 04:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(3, 'fatima.sheikh', 'fatima.sheikh@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Fatima Sheikh', '+92-322-3456789', 1, 3, 1, '2025-08-11 06:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(4, 'ali.hassan', 'ali.hassan@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Ali Hassan', '+92-323-4567890', 1, 4, 1, '2025-08-12 03:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(5, 'zara.malik', 'zara.malik@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Zara Malik', '+92-324-5678901', 1, 6, 1, '2025-08-12 01:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(6, 'hassan.shah', 'hassan.shah@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Muhammad Hassan Shah', '+92-325-6789012', 2, 2, 1, '2025-08-12 05:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(7, 'ayesha.khan', 'ayesha.khan@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Ayesha Khan', '+92-326-7890123', 2, 4, 1, '2025-08-10 06:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(8, 'usman.ali', 'usman.ali@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Usman Ali', '+92-327-8901234', 2, 7, 1, '2025-08-12 00:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(9, 'sarah.malik', 'sarah.malik@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Sarah Ahmed Malik', '+92-328-9012345', 3, 2, 1, '2025-08-12 02:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(10, 'omar.farooq', 'omar.farooq@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Omar Farooq', '+92-329-0123456', 3, 4, 1, '2025-08-11 06:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(11, 'tariq.qureshi', 'tariq.qureshi@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Tariq Mahmood Qureshi', '+92-330-1234567', 4, 2, 1, '2025-08-12 03:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(12, 'sana.ahmed', 'sana.ahmed@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Sana Ahmed', '+92-331-2345678', 4, 5, 1, '2025-08-11 23:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(13, 'nasir.fatima', 'nasir.fatima@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Fatima Nasir', '+92-332-3456789', 5, 2, 1, '2025-08-10 06:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(14, 'bilal.ahmed', 'bilal.ahmed@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Bilal Ahmed', '+92-333-4567890', 5, 4, 1, '2025-08-11 22:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(15, 'imran.shah', 'imran.shah@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Imran Shah', '+92-334-5678901', 6, 4, 1, '2025-08-11 06:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05'),
(16, 'khadija.noor', 'khadija.noor@techcorp.pk', '$2y$10$92IXUNpkjO0rOQ5byMi.Ye4oKoEa3Ro9llC/.og/at2.uheWG/igi', 'Khadija Noor', '+92-335-6789012', 7, 5, 1, '2025-08-09 06:31:05', '2025-08-12 06:31:05', '2025-08-12 06:31:05');

--
-- Triggers `users`
--
DELIMITER $$
CREATE TRIGGER `user_activity_log` AFTER UPDATE ON `users` FOR EACH ROW BEGIN
    INSERT INTO system_logs (user_id, action, table_affected, record_id, old_values, new_values)
    VALUES (NEW.user_id, 'UPDATE', 'users', NEW.user_id, 
            JSON_OBJECT('last_login', OLD.last_login),
            JSON_OBJECT('last_login', NEW.last_login));
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Stand-in structure for view `v_current_stock`
-- (See below for the actual view)
--
CREATE TABLE `v_current_stock` (
`item_id` int(11)
,`item_name` varchar(200)
,`item_code` varchar(50)
,`category_name` varchar(100)
,`branch_name` varchar(100)
,`branch_code` varchar(10)
,`current_stock` int(11)
,`reserved_stock` int(11)
,`available_stock` int(11)
,`minimum_stock_level` int(11)
,`stock_status` varchar(12)
,`last_updated` timestamp
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `v_low_stock_alerts`
-- (See below for the actual view)
--
CREATE TABLE `v_low_stock_alerts` (
`item_name` varchar(200)
,`item_code` varchar(50)
,`branch_name` varchar(100)
,`current_stock` int(11)
,`available_stock` int(11)
,`minimum_stock_level` int(11)
,`shortage_quantity` bigint(12)
);

-- --------------------------------------------------------

--
-- Stand-in structure for view `v_transfer_summary`
-- (See below for the actual view)
--
CREATE TABLE `v_transfer_summary` (
`transfer_id` int(11)
,`transfer_number` varchar(50)
,`from_branch` varchar(100)
,`to_branch` varchar(100)
,`requested_by_name` varchar(100)
,`status` enum('PENDING','APPROVED','REJECTED','IN_TRANSIT','DELIVERED','CANCELLED')
,`priority` enum('LOW','MEDIUM','HIGH','URGENT')
,`total_items` bigint(21)
,`total_requested_qty` decimal(32,0)
,`total_approved_qty` decimal(32,0)
,`request_date` timestamp
,`approval_date` timestamp
,`dispatch_date` timestamp
,`delivery_date` timestamp
);

-- --------------------------------------------------------

--
-- Structure for view `v_current_stock`
--
DROP TABLE IF EXISTS `v_current_stock`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_current_stock`  AS SELECT `i`.`item_id` AS `item_id`, `i`.`item_name` AS `item_name`, `i`.`item_code` AS `item_code`, `c`.`category_name` AS `category_name`, `b`.`branch_name` AS `branch_name`, `b`.`branch_code` AS `branch_code`, `inv`.`current_stock` AS `current_stock`, `inv`.`reserved_stock` AS `reserved_stock`, `inv`.`available_stock` AS `available_stock`, `i`.`minimum_stock_level` AS `minimum_stock_level`, CASE WHEN `inv`.`available_stock` <= `i`.`minimum_stock_level` THEN 'LOW' WHEN `inv`.`available_stock` = 0 THEN 'OUT_OF_STOCK' ELSE 'NORMAL' END AS `stock_status`, `inv`.`last_updated` AS `last_updated` FROM (((`inventory` `inv` join `items` `i` on(`inv`.`item_id` = `i`.`item_id`)) join `categories` `c` on(`i`.`category_id` = `c`.`category_id`)) join `branches` `b` on(`inv`.`branch_id` = `b`.`branch_id`)) WHERE `i`.`is_active` = 1 AND `b`.`is_active` = 1 ;

-- --------------------------------------------------------

--
-- Structure for view `v_low_stock_alerts`
--
DROP TABLE IF EXISTS `v_low_stock_alerts`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_low_stock_alerts`  AS SELECT `i`.`item_name` AS `item_name`, `i`.`item_code` AS `item_code`, `b`.`branch_name` AS `branch_name`, `inv`.`current_stock` AS `current_stock`, `inv`.`available_stock` AS `available_stock`, `i`.`minimum_stock_level` AS `minimum_stock_level`, `i`.`minimum_stock_level`- `inv`.`available_stock` AS `shortage_quantity` FROM ((`inventory` `inv` join `items` `i` on(`inv`.`item_id` = `i`.`item_id`)) join `branches` `b` on(`inv`.`branch_id` = `b`.`branch_id`)) WHERE `inv`.`available_stock` <= `i`.`minimum_stock_level` AND `i`.`is_active` = 1 AND `b`.`is_active` = 1 ORDER BY `i`.`minimum_stock_level`- `inv`.`available_stock` DESC ;

-- --------------------------------------------------------

--
-- Structure for view `v_transfer_summary`
--
DROP TABLE IF EXISTS `v_transfer_summary`;

CREATE ALGORITHM=UNDEFINED DEFINER=`root`@`localhost` SQL SECURITY DEFINER VIEW `v_transfer_summary`  AS SELECT `tr`.`transfer_id` AS `transfer_id`, `tr`.`transfer_number` AS `transfer_number`, `fb`.`branch_name` AS `from_branch`, `tb`.`branch_name` AS `to_branch`, `u`.`full_name` AS `requested_by_name`, `tr`.`status` AS `status`, `tr`.`priority` AS `priority`, count(`tri`.`request_item_id`) AS `total_items`, sum(`tri`.`requested_quantity`) AS `total_requested_qty`, sum(`tri`.`approved_quantity`) AS `total_approved_qty`, `tr`.`request_date` AS `request_date`, `tr`.`approval_date` AS `approval_date`, `tr`.`dispatch_date` AS `dispatch_date`, `tr`.`delivery_date` AS `delivery_date` FROM ((((`transfer_requests` `tr` join `branches` `fb` on(`tr`.`from_branch_id` = `fb`.`branch_id`)) join `branches` `tb` on(`tr`.`to_branch_id` = `tb`.`branch_id`)) join `users` `u` on(`tr`.`requested_by` = `u`.`user_id`)) left join `transfer_request_items` `tri` on(`tr`.`transfer_id` = `tri`.`transfer_id`)) GROUP BY `tr`.`transfer_id` ;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `branches`
--
ALTER TABLE `branches`
  ADD PRIMARY KEY (`branch_id`),
  ADD UNIQUE KEY `branch_code` (`branch_code`);

--
-- Indexes for table `categories`
--
ALTER TABLE `categories`
  ADD PRIMARY KEY (`category_id`),
  ADD UNIQUE KEY `category_code` (`category_code`);

--
-- Indexes for table `dispatch_slips`
--
ALTER TABLE `dispatch_slips`
  ADD PRIMARY KEY (`dispatch_id`),
  ADD UNIQUE KEY `dispatch_number` (`dispatch_number`),
  ADD KEY `transfer_id` (`transfer_id`),
  ADD KEY `dispatched_by` (`dispatched_by`);

--
-- Indexes for table `inventory`
--
ALTER TABLE `inventory`
  ADD PRIMARY KEY (`inventory_id`),
  ADD UNIQUE KEY `unique_item_branch` (`item_id`,`branch_id`),
  ADD KEY `updated_by` (`updated_by`),
  ADD KEY `idx_inventory_item_branch` (`item_id`,`branch_id`),
  ADD KEY `idx_inventory_branch` (`branch_id`),
  ADD KEY `idx_inventory_low_stock` (`item_id`,`branch_id`,`available_stock`);

--
-- Indexes for table `items`
--
ALTER TABLE `items`
  ADD PRIMARY KEY (`item_id`),
  ADD UNIQUE KEY `item_code` (`item_code`),
  ADD KEY `category_id` (`category_id`);

--
-- Indexes for table `receiving_slips`
--
ALTER TABLE `receiving_slips`
  ADD PRIMARY KEY (`receiving_id`),
  ADD UNIQUE KEY `receiving_number` (`receiving_number`),
  ADD KEY `transfer_id` (`transfer_id`),
  ADD KEY `dispatch_id` (`dispatch_id`),
  ADD KEY `received_by` (`received_by`);

--
-- Indexes for table `receiving_slip_items`
--
ALTER TABLE `receiving_slip_items`
  ADD PRIMARY KEY (`receiving_item_id`),
  ADD KEY `receiving_id` (`receiving_id`),
  ADD KEY `item_id` (`item_id`);

--
-- Indexes for table `roles`
--
ALTER TABLE `roles`
  ADD PRIMARY KEY (`role_id`),
  ADD UNIQUE KEY `role_name` (`role_name`);

--
-- Indexes for table `stock_discrepancies`
--
ALTER TABLE `stock_discrepancies`
  ADD PRIMARY KEY (`discrepancy_id`),
  ADD KEY `branch_id` (`branch_id`),
  ADD KEY `item_id` (`item_id`),
  ADD KEY `reported_by` (`reported_by`);

--
-- Indexes for table `stock_movements`
--
ALTER TABLE `stock_movements`
  ADD PRIMARY KEY (`movement_id`),
  ADD KEY `created_by` (`created_by`),
  ADD KEY `idx_stock_movements_item` (`item_id`),
  ADD KEY `idx_stock_movements_branch` (`branch_id`),
  ADD KEY `idx_stock_movements_date` (`created_at`),
  ADD KEY `idx_stock_movements_type` (`movement_type`);

--
-- Indexes for table `system_logs`
--
ALTER TABLE `system_logs`
  ADD PRIMARY KEY (`log_id`),
  ADD KEY `user_id` (`user_id`);

--
-- Indexes for table `transfer_requests`
--
ALTER TABLE `transfer_requests`
  ADD PRIMARY KEY (`transfer_id`),
  ADD UNIQUE KEY `transfer_number` (`transfer_number`),
  ADD KEY `to_branch_id` (`to_branch_id`),
  ADD KEY `requested_by` (`requested_by`),
  ADD KEY `approved_by` (`approved_by`),
  ADD KEY `idx_transfer_status` (`status`),
  ADD KEY `idx_transfer_branches` (`from_branch_id`,`to_branch_id`),
  ADD KEY `idx_transfer_date` (`request_date`);

--
-- Indexes for table `transfer_request_items`
--
ALTER TABLE `transfer_request_items`
  ADD PRIMARY KEY (`request_item_id`),
  ADD KEY `transfer_id` (`transfer_id`),
  ADD KEY `item_id` (`item_id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`user_id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD UNIQUE KEY `email` (`email`),
  ADD KEY `idx_users_branch` (`branch_id`),
  ADD KEY `idx_users_role` (`role_id`),
  ADD KEY `idx_users_active` (`is_active`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `branches`
--
ALTER TABLE `branches`
  MODIFY `branch_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=9;

--
-- AUTO_INCREMENT for table `categories`
--
ALTER TABLE `categories`
  MODIFY `category_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `dispatch_slips`
--
ALTER TABLE `dispatch_slips`
  MODIFY `dispatch_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=6;

--
-- AUTO_INCREMENT for table `inventory`
--
ALTER TABLE `inventory`
  MODIFY `inventory_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=236;

--
-- AUTO_INCREMENT for table `items`
--
ALTER TABLE `items`
  MODIFY `item_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=28;

--
-- AUTO_INCREMENT for table `receiving_slips`
--
ALTER TABLE `receiving_slips`
  MODIFY `receiving_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- AUTO_INCREMENT for table `receiving_slip_items`
--
ALTER TABLE `receiving_slip_items`
  MODIFY `receiving_item_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=10;

--
-- AUTO_INCREMENT for table `roles`
--
ALTER TABLE `roles`
  MODIFY `role_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `stock_discrepancies`
--
ALTER TABLE `stock_discrepancies`
  MODIFY `discrepancy_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

--
-- AUTO_INCREMENT for table `stock_movements`
--
ALTER TABLE `stock_movements`
  MODIFY `movement_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=15;

--
-- AUTO_INCREMENT for table `system_logs`
--
ALTER TABLE `system_logs`
  MODIFY `log_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=8;

--
-- AUTO_INCREMENT for table `transfer_requests`
--
ALTER TABLE `transfer_requests`
  MODIFY `transfer_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=11;

--
-- AUTO_INCREMENT for table `transfer_request_items`
--
ALTER TABLE `transfer_request_items`
  MODIFY `request_item_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=55;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `user_id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=17;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `dispatch_slips`
--
ALTER TABLE `dispatch_slips`
  ADD CONSTRAINT `dispatch_slips_ibfk_1` FOREIGN KEY (`transfer_id`) REFERENCES `transfer_requests` (`transfer_id`),
  ADD CONSTRAINT `dispatch_slips_ibfk_2` FOREIGN KEY (`dispatched_by`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `inventory`
--
ALTER TABLE `inventory`
  ADD CONSTRAINT `inventory_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`),
  ADD CONSTRAINT `inventory_ibfk_2` FOREIGN KEY (`branch_id`) REFERENCES `branches` (`branch_id`),
  ADD CONSTRAINT `inventory_ibfk_3` FOREIGN KEY (`updated_by`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `items`
--
ALTER TABLE `items`
  ADD CONSTRAINT `items_ibfk_1` FOREIGN KEY (`category_id`) REFERENCES `categories` (`category_id`);

--
-- Constraints for table `receiving_slips`
--
ALTER TABLE `receiving_slips`
  ADD CONSTRAINT `receiving_slips_ibfk_1` FOREIGN KEY (`transfer_id`) REFERENCES `transfer_requests` (`transfer_id`),
  ADD CONSTRAINT `receiving_slips_ibfk_2` FOREIGN KEY (`dispatch_id`) REFERENCES `dispatch_slips` (`dispatch_id`),
  ADD CONSTRAINT `receiving_slips_ibfk_3` FOREIGN KEY (`received_by`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `receiving_slip_items`
--
ALTER TABLE `receiving_slip_items`
  ADD CONSTRAINT `receiving_slip_items_ibfk_1` FOREIGN KEY (`receiving_id`) REFERENCES `receiving_slips` (`receiving_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `receiving_slip_items_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`);

--
-- Constraints for table `stock_discrepancies`
--
ALTER TABLE `stock_discrepancies`
  ADD CONSTRAINT `stock_discrepancies_ibfk_1` FOREIGN KEY (`branch_id`) REFERENCES `branches` (`branch_id`),
  ADD CONSTRAINT `stock_discrepancies_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`),
  ADD CONSTRAINT `stock_discrepancies_ibfk_3` FOREIGN KEY (`reported_by`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `stock_movements`
--
ALTER TABLE `stock_movements`
  ADD CONSTRAINT `stock_movements_ibfk_1` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`),
  ADD CONSTRAINT `stock_movements_ibfk_2` FOREIGN KEY (`branch_id`) REFERENCES `branches` (`branch_id`),
  ADD CONSTRAINT `stock_movements_ibfk_3` FOREIGN KEY (`created_by`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `system_logs`
--
ALTER TABLE `system_logs`
  ADD CONSTRAINT `system_logs_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `transfer_requests`
--
ALTER TABLE `transfer_requests`
  ADD CONSTRAINT `transfer_requests_ibfk_1` FOREIGN KEY (`from_branch_id`) REFERENCES `branches` (`branch_id`),
  ADD CONSTRAINT `transfer_requests_ibfk_2` FOREIGN KEY (`to_branch_id`) REFERENCES `branches` (`branch_id`),
  ADD CONSTRAINT `transfer_requests_ibfk_3` FOREIGN KEY (`requested_by`) REFERENCES `users` (`user_id`),
  ADD CONSTRAINT `transfer_requests_ibfk_4` FOREIGN KEY (`approved_by`) REFERENCES `users` (`user_id`);

--
-- Constraints for table `transfer_request_items`
--
ALTER TABLE `transfer_request_items`
  ADD CONSTRAINT `transfer_request_items_ibfk_1` FOREIGN KEY (`transfer_id`) REFERENCES `transfer_requests` (`transfer_id`) ON DELETE CASCADE,
  ADD CONSTRAINT `transfer_request_items_ibfk_2` FOREIGN KEY (`item_id`) REFERENCES `items` (`item_id`);

--
-- Constraints for table `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`branch_id`) REFERENCES `branches` (`branch_id`),
  ADD CONSTRAINT `users_ibfk_2` FOREIGN KEY (`role_id`) REFERENCES `roles` (`role_id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
