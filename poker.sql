-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Servidor: 127.0.0.1
-- Tiempo de generación: 03-06-2025 a las 22:20:15
-- Versión del servidor: 10.4.32-MariaDB
-- Versión de PHP: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Base de datos: `poker`
--

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `games`
--

CREATE TABLE `games` (
  `id` int(11) NOT NULL,
  `table_id` int(11) NOT NULL,
  `start_time` datetime NOT NULL DEFAULT current_timestamp(),
  `end_time` datetime DEFAULT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `game_histories`
--

CREATE TABLE `game_histories` (
  `id` int(11) NOT NULL,
  `game_id` int(11) NOT NULL,
  `player_id` int(11) NOT NULL,
  `round` int(11) NOT NULL,
  `pot` int(11) NOT NULL,
  `points` int(11) NOT NULL DEFAULT 0,
  `result` varchar(5) DEFAULT NULL,
  `street` varchar(8) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `levels`
--

CREATE TABLE `levels` (
  `id` int(11) NOT NULL,
  `name` varchar(50) NOT NULL,
  `blind_min` int(11) NOT NULL,
  `blind_max` int(11) NOT NULL,
  `required_points` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `levels`
--

INSERT INTO `levels` (`id`, `name`, `blind_min`, `blind_max`, `required_points`, `created_at`) VALUES
(1, 'Novice', 1, 10, 0, '2025-06-02 22:09:15'),
(2, 'Apprentice', 5, 20, 1000, '2025-06-02 22:09:15'),
(3, 'Enthusiast', 10, 50, 5000, '2025-06-02 22:09:15'),
(4, 'Casual Player', 25, 100, 15000, '2025-06-02 22:09:15'),
(5, 'Expert Player', 50, 200, 50000, '2025-06-02 22:09:15'),
(6, 'Shark', 100, 500, 100000, '2025-06-02 22:09:15'),
(7, 'Local Legend', 250, 1000, 250000, '2025-06-02 22:09:15'),
(8, 'National Champion', 500, 2000, 500000, '2025-06-02 22:09:15'),
(9, 'Grand Poker Master', 1000, 5000, 1000000, '2025-06-02 22:09:15'),
(10, 'Poker Legend', 2500, 10000, 2500000, '2025-06-02 22:09:15');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `players`
--

CREATE TABLE `players` (
  `id` int(11) NOT NULL,
  `level_id` int(11) DEFAULT NULL,
  `balance` int(11) NOT NULL DEFAULT 1000,
  `stack` int(11) NOT NULL DEFAULT 0,
  `total_points` int(11) NOT NULL DEFAULT 0,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `players`
--

INSERT INTO `players` (`id`, `level_id`, `balance`, `stack`, `total_points`, `created_at`) VALUES
(1, 1, 1000, 0, 0, '2025-06-02 22:09:15'),
(2, 1, 1000, 0, 0, '2025-06-02 22:09:15'),
(3, 1, 1000, 0, 0, '2025-06-02 22:09:15');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `round_histories`
--

CREATE TABLE `round_histories` (
  `id` int(11) NOT NULL,
  `game_id` int(11) NOT NULL,
  `player_id` int(11) NOT NULL,
  `round` int(11) NOT NULL,
  `bet` int(11) NOT NULL,
  `action` varchar(10) NOT NULL,
  `street` varchar(8) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `tables`
--

CREATE TABLE `tables` (
  `id` int(11) NOT NULL,
  `name` varchar(100) NOT NULL,
  `owner_id` int(11) NOT NULL,
  `blind` int(11) NOT NULL,
  `level_id` int(11) NOT NULL,
  `max_players` int(11) NOT NULL,
  `required_stack` int(11) NOT NULL,
  `created_at` datetime DEFAULT current_timestamp()
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `tables`
--

INSERT INTO `tables` (`id`, `name`, `owner_id`, `blind`, `level_id`, `max_players`, `required_stack`, `created_at`) VALUES
(1, 'Table Russell Group Novice', 2, 4, 1, 6, 46, '2025-06-02 22:09:15'),
(2, 'Table Greene, Lee and Vasquez Novice', 2, 5, 1, 5, 74, '2025-06-02 22:09:15'),
(3, 'Table Norman Inc Novice', 3, 4, 1, 7, 46, '2025-06-02 22:09:15'),
(4, 'Table Sanchez, Lee and Hammond Apprentice', 1, 11, 2, 7, 56, '2025-06-02 22:09:15'),
(5, 'Table Gentry LLC Apprentice', 3, 10, 2, 4, 75, '2025-06-02 22:09:15'),
(6, 'Table Castillo Inc Apprentice', 2, 19, 2, 3, 120, '2025-06-02 22:09:15'),
(7, 'Table Anderson, Avila and Cox Enthusiast', 3, 19, 3, 3, 481, '2025-06-02 22:09:15'),
(8, 'Table Hunt Group Enthusiast', 1, 23, 3, 7, 443, '2025-06-02 22:09:15'),
(9, 'Table Castro, Nash and Hughes Enthusiast', 3, 48, 3, 5, 492, '2025-06-02 22:09:15'),
(10, 'Table Rodriguez, Coleman and Parsons Casual Player', 2, 54, 4, 5, 496, '2025-06-02 22:09:15'),
(11, 'Table Roberts-Byrd Casual Player', 1, 33, 4, 3, 510, '2025-06-02 22:09:15'),
(12, 'Table Hughes Inc Casual Player', 3, 68, 4, 6, 385, '2025-06-02 22:09:15'),
(13, 'Table Davis, Fuentes and Rivera Expert Player', 1, 86, 5, 6, 1962, '2025-06-02 22:09:15'),
(14, 'Table Gonzalez, Ellis and Hatfield Expert Player', 3, 108, 5, 6, 1119, '2025-06-02 22:09:15'),
(15, 'Table Christian Inc Expert Player', 1, 136, 5, 5, 734, '2025-06-02 22:09:15'),
(16, 'Table Monroe, Frank and Dixon Shark', 3, 193, 6, 6, 1857, '2025-06-02 22:09:15'),
(17, 'Table Dunn, Ray and Roberts Shark', 2, 493, 6, 4, 1999, '2025-06-02 22:09:15'),
(18, 'Table Horton-Williams Shark', 2, 222, 6, 5, 4398, '2025-06-02 22:09:15'),
(19, 'Table Huff Inc Local Legend', 2, 435, 7, 7, 8296, '2025-06-02 22:09:15'),
(20, 'Table Lowe Ltd Local Legend', 2, 340, 7, 6, 4201, '2025-06-02 22:09:15'),
(21, 'Table Ward PLC Local Legend', 2, 415, 7, 3, 3833, '2025-06-02 22:09:15'),
(22, 'Table Richards PLC National Champion', 3, 688, 8, 6, 15483, '2025-06-02 22:09:15'),
(23, 'Table Sawyer-Gonzalez National Champion', 1, 1450, 8, 3, 13362, '2025-06-02 22:09:15'),
(24, 'Table Dawson-Robinson National Champion', 2, 1175, 8, 5, 7318, '2025-06-02 22:09:15'),
(25, 'Table Burnett, Roberts and Keller Grand Poker Master', 2, 1120, 9, 6, 35846, '2025-06-02 22:09:15'),
(26, 'Table Jimenez-Hardy Grand Poker Master', 1, 1143, 9, 6, 31707, '2025-06-02 22:09:15'),
(27, 'Table Garcia-Parker Grand Poker Master', 1, 1613, 9, 7, 23593, '2025-06-02 22:09:15'),
(28, 'Table Brown-Tanner Poker Legend', 1, 2815, 10, 4, 84007, '2025-06-02 22:09:15'),
(29, 'Table Robles Group Poker Legend', 1, 5642, 10, 7, 41003, '2025-06-02 22:09:15'),
(30, 'Table Benson, Marquez and Bell Poker Legend', 3, 3321, 10, 6, 87966, '2025-06-02 22:09:15');

-- --------------------------------------------------------

--
-- Estructura de tabla para la tabla `users`
--

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `full_name` varchar(150) NOT NULL,
  `username` varchar(80) NOT NULL,
  `password_hash` varchar(255) NOT NULL,
  `created_at` datetime NOT NULL DEFAULT current_timestamp(),
  `email` varchar(120) NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Volcado de datos para la tabla `users`
--

INSERT INTO `users` (`id`, `full_name`, `username`, `password_hash`, `created_at`, `email`) VALUES
(1, 'Super Admin', 'admin', 'scrypt:32768:8:1$xb4AOazHiQU5yWsF$bd83150c6b8319f008d47c179576cf220bd98ca59e180b2c9f128c67b05798196520d342bcff6dc2c1f04977579a57315162c11f5e0b64e043b8baa3b1d18e83', '2025-06-02 22:09:15', 'admin2@admin.com'),
(2, 'Michelle Cannon', 'jross', 'scrypt:32768:8:1$qj3rd5ukNO3mYqrk$58d3c14ecda7fe19dd16081763cbfa2260e8b2c92ead15ec7f2b257a5f97a658c4a195095be5e9c4c345efaaec0261b18658b3485da04987d7c5af8f565d06cc', '2025-06-02 22:09:15', 'johnsonjesus@example.com'),
(3, 'Devin Williams', 'adamsgregory', 'scrypt:32768:8:1$XglvaUqVXnpH7wfY$c4002aeab9c0f8a5ced7b6b63d1957012e557110d155022093f3f36b38944d8af27e5b27fd00bf3f2b395bd2792e7cd31a2cd854b41fcf2d298c923091bbbc1b', '2025-06-02 22:09:15', 'jason18@example.org');

--
-- Índices para tablas volcadas
--

--
-- Indices de la tabla `games`
--
ALTER TABLE `games`
  ADD PRIMARY KEY (`id`),
  ADD KEY `table_id` (`table_id`);

--
-- Indices de la tabla `game_histories`
--
ALTER TABLE `game_histories`
  ADD PRIMARY KEY (`id`),
  ADD KEY `game_id` (`game_id`),
  ADD KEY `player_id` (`player_id`);

--
-- Indices de la tabla `levels`
--
ALTER TABLE `levels`
  ADD PRIMARY KEY (`id`);

--
-- Indices de la tabla `players`
--
ALTER TABLE `players`
  ADD PRIMARY KEY (`id`),
  ADD KEY `level_id` (`level_id`);

--
-- Indices de la tabla `round_histories`
--
ALTER TABLE `round_histories`
  ADD PRIMARY KEY (`id`),
  ADD KEY `game_id` (`game_id`),
  ADD KEY `player_id` (`player_id`);

--
-- Indices de la tabla `tables`
--
ALTER TABLE `tables`
  ADD PRIMARY KEY (`id`),
  ADD KEY `owner_id` (`owner_id`),
  ADD KEY `level_id` (`level_id`);

--
-- Indices de la tabla `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT de las tablas volcadas
--

--
-- AUTO_INCREMENT de la tabla `games`
--
ALTER TABLE `games`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=24;

--
-- AUTO_INCREMENT de la tabla `game_histories`
--
ALTER TABLE `game_histories`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `round_histories`
--
ALTER TABLE `round_histories`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT de la tabla `tables`
--
ALTER TABLE `tables`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=31;

--
-- AUTO_INCREMENT de la tabla `users`
--
ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=4;

--
-- Restricciones para tablas volcadas
--

--
-- Filtros para la tabla `games`
--
ALTER TABLE `games`
  ADD CONSTRAINT `games_ibfk_1` FOREIGN KEY (`table_id`) REFERENCES `tables` (`id`);

--
-- Filtros para la tabla `game_histories`
--
ALTER TABLE `game_histories`
  ADD CONSTRAINT `game_histories_ibfk_1` FOREIGN KEY (`game_id`) REFERENCES `games` (`id`),
  ADD CONSTRAINT `game_histories_ibfk_2` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`);

--
-- Filtros para la tabla `players`
--
ALTER TABLE `players`
  ADD CONSTRAINT `players_ibfk_1` FOREIGN KEY (`id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `players_ibfk_2` FOREIGN KEY (`level_id`) REFERENCES `levels` (`id`);

--
-- Filtros para la tabla `round_histories`
--
ALTER TABLE `round_histories`
  ADD CONSTRAINT `round_histories_ibfk_1` FOREIGN KEY (`game_id`) REFERENCES `games` (`id`),
  ADD CONSTRAINT `round_histories_ibfk_2` FOREIGN KEY (`player_id`) REFERENCES `players` (`id`);

--
-- Filtros para la tabla `tables`
--
ALTER TABLE `tables`
  ADD CONSTRAINT `tables_ibfk_1` FOREIGN KEY (`owner_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `tables_ibfk_2` FOREIGN KEY (`level_id`) REFERENCES `levels` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
