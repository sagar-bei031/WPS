SELECT * FROM locations l ;
SELECT * FROM ssids s;
SELECT * FROM scans sc;
SELECT * FROM wifi_signals ws;

--- find no. of total wifi signal count at all locations
SELECT l.id AS location_id, l.location_name, COUNT(ws.id) AS wifi_signal_count
FROM locations l
JOIN scans sc ON l.id = sc.location_id
JOIN wifi_signals ws ON sc.id = ws.scan_id
GROUP BY l.id, l.location_name;

-- Find the number of unique Wi-Fi signals scanned at all locations
SELECT l.id AS location_id, l.location_name, COUNT(DISTINCT ws.ssid_id) AS unique_wifi_signal_count
FROM locations l
JOIN scans sc ON l.id = sc.location_id
JOIN wifi_signals ws ON sc.id = ws.scan_id
GROUP BY l.id, l.location_name;