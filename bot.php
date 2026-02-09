<?php

require_once "config.php";

$token = "8426836407:AAHoXkQakddqyXZ_olNplG0_ov-3fhvrkSc";
$admin = 5775388579;

$update = json_decode(file_get_contents("php://input"), true);

$message = $update["message"] ?? null;
$text = $message["text"] ?? null;
$chat_id = $message["chat"]["id"] ?? null;
$user_id = $message["from"]["id"] ?? null;
$video = $message["video"]["file_id"] ?? null;

function bot($method,$data){
    global $token;
    $url = "https://api.telegram.org/bot$token/$method";

    $ch = curl_init();
    curl_setopt($ch,CURLOPT_URL,$url);
    curl_setopt($ch,CURLOPT_POST,true);
    curl_setopt($ch,CURLOPT_POSTFIELDS,$data);
    curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);

    curl_exec($ch);
    curl_close($ch);
}

# ===== DATABASE TABLES =====
$conn->query("CREATE TABLE IF NOT EXISTS movies(
    code VARCHAR(50) PRIMARY KEY,
    file_id TEXT,
    name TEXT
)");

$conn->query("CREATE TABLE IF NOT EXISTS users(
    user_id BIGINT PRIMARY KEY
)");

# ===== USER SAQLASH =====
if($user_id){
    $conn->query("INSERT IGNORE INTO users(user_id) VALUES('$user_id')");
}

# ===== ADMIN =====
if($text == "/start"){

    if($user_id == $admin){

        bot("sendMessage",[
            "chat_id"=>$chat_id,
            "text"=>"🔥 ADMIN PANEL\n\nKod yuboring -> keyin video -> keyin nom"
        ]);

    }else{

        bot("sendMessage",[
            "chat_id"=>$chat_id,
            "text"=>"🎬 Kino kodini yuboring:"
        ]);
    }
}

# ===== KINO QO‘SHISH (oddiy GOD MODE) =====

$step_file = "step.txt";

if($user_id == $admin){

    if(is_numeric($text)){
        file_put_contents($step_file,$text);

        bot("sendMessage",[
            "chat_id"=>$chat_id,
            "text"=>"✅ Endi videoni yuboring"
        ]);
    }

    elseif($video){

        $code = file_get_contents($step_file);
        file_put_contents("video.txt",$video);

        bot("sendMessage",[
            "chat_id"=>$chat_id,
            "text"=>"🎬 Kino nomini yozing"
        ]);
    }

    elseif(file_exists("video.txt")){

        $code = file_get_contents($step_file);
        $file_id = file_get_contents("video.txt");
        $name = $text;

        $stmt = $conn->prepare("INSERT INTO movies(code,file_id,name) VALUES(?,?,?) ON DUPLICATE KEY UPDATE file_id=?, name=?");
        $stmt->bind_param("sssss",$code,$file_id,$name,$file_id,$name);
        $stmt->execute();

        unlink("video.txt");

        bot("sendMessage",[
            "chat_id"=>$chat_id,
            "text"=>"✅ Kino saqlandi va UCHMAYDI 🔥"
        ]);
    }
}

# ===== USER KINO OLISH =====

if(is_numeric($text) AND $user_id != $admin){

    $result = $conn->query("SELECT * FROM movies WHERE code='$text'");

    if($result->num_rows){

        $movie = $result->fetch_assoc();

        bot("sendVideo",[
            "chat_id"=>$chat_id,
            "video"=>$movie["file_id"],
            "caption"=>"🎬 ".$movie["name"]
        ]);

    }else{

        bot("sendMessage",[
            "chat_id"=>$chat_id,
            "text"=>"❌ Kino topilmadi"
        ]);
    }
}

?>
