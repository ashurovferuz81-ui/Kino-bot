<?php

$host = "mysql.railway.internal";
$user = "root";
$password = "LHIbMgHXslFIakBWstIPSpdQcqCgZfev";
$database = "railway";

$conn = new mysqli($host, $user, $password, $database);

if ($conn->connect_error) {
    die("DB ulanmadI: " . $conn->connect_error);
}

?>
