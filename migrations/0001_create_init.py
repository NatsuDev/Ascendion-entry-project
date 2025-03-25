from yoyo import step

steps = [
    step(
        """
        CREATE TABLE IF NOT EXISTS `products` (
            `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT,
            `name` varchar(50) NOT NULL,
            `description` TEXT NOT NULL,
            `price` double UNSIGNED NOT NULL,
            `image_url` varchar(250) DEFAULT NULL,
            PRIMARY KEY (`id`)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
        """,
        """
        DROP TABLE IF EXISTS `products`;
        """,
    ),
]
