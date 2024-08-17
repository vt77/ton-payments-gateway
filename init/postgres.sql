DROP TABLE IF EXISTS `invoices`;
CREATE TABLE `invoices` (
  `id` VARCHAR(64) NOT NULL,
  `amount` INT(16) NOT NULL,
  `srcpurse` VARCHAR(128) NOT NULL,
  `dstpurse` VARCHAR(128) NOT NULL,
  `status` ENUM ('pending','completed','expired','error')  NOT NULL DEFAULT 'pending',
  `context` VARCHAR(128) NOT NULL,
  `created` DATETIME DEFAULT UTC_TIMESTAMP(),
  `last_update` DATETIME DEFAULT NULL,
  `expired` DATETIME NOT NULL,
  `transaction` VARCHAR(128) DEFAULT NULL,
  PRIMARY KEY (id),
  INDEX `dst_purse_idx` (`dstpurse`)
) ENGINE=MyISAM DEFAULT CHARSET=utf8;
