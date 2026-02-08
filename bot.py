<?php
// Sizning Telegram bot tokeningiz va admin ID
define('API_KEY','8501918863:AAE6YCS4j3z0JM9RcpmNXVtk2Kh1qUfABRQ');

$idbot = '8501918863';
$admin = '5775388579'; // Sizning Telegram ID’ingiz
$owners = array($admin);
$user = "Sardorbeko008";
$bot=bot(getMe)->result->username;

// Railway DB sozlamalari (Environment variables orqali)
$connect = mysqli_connect(getenv("DB_HOST"), getenv("DB_USER"), getenv("DB_PASS"), getenv("DB_NAME"));
mysqli_set_charset($connect, 'utf8mb4');

if ($connect->connect_error) {
    die("<h2 style='color:red;'>❌ SQL baza ulanmagan! Xatolik: " . $connect->connect_error . "</h2>");
}

// Bot funksiyalari
function bot($method,$datas=[]){
    $url = "https://api.telegram.org/bot". API_KEY ."/". $method;
    $ch = curl_init();
    curl_setopt($ch,CURLOPT_URL,$url);
    curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
    curl_setopt($ch,CURLOPT_POSTFIELDS,$datas);
    $res = curl_exec($ch);
    if(curl_error($ch)) var_dump(curl_error($ch));
    else return json_decode($res);
}

function sendMessage($id, $text, $key = null){
    return bot('sendMessage',[
        'chat_id'=>$id,
        'text'=>$text,
        'parse_mode'=>'html',
        'disable_web_page_preview'=>true,
        'reply_markup'=>$key
    ]);
}

function getChatMember($cid, $userid){
    return bot('getChatMember',[
        'chat_id'=>$cid,
        'user_id'=>$userid
    ]);
}

// Majburiy obuna
function joinchat($id){
    $channel = "@kinomandabor"; // Majburiy kanal
    $key = [
        'inline_keyboard' => [
            [['text'=>"❌ Kanalga obuna bo‘ling", 'url'=>"https://t.me/kinomandabor"]],
            [['text'=>"Obuna bo'ldim ✅", 'callback_data'=>"check"]]
        ]
    ];
    $ret = getChatMember($channel, $id);
    if(isset($ret->result->status) && in_array($ret->result->status, ["member","administrator","creator"])){
        return true;
    } else {
        sendMessage($id,"❌ <b>Botdan to'liq foydalanish uchun kanalga obuna bo'ling!</b>", json_encode($key));
        return false;
    }
}

// Update olish
$update = json_decode(file_get_contents('php://input'));

$message = $update->message ?? null;
$callback = $update->callback_query ?? null;

if(isset($message)){
    $cid = $message->chat->id;
    $text = $message->text;
}

if(isset($callback)){
    $cid = $callback->message->chat->id;
    $mid = $callback->message->message_id;
    $from_id = $callback->from->id;
    $data = $callback->data;
}

// Callback: Obuna tekshirish
if(isset($data) && $data == "check"){
    $channel = "@kinomandabor";
    $ret = getChatMember($channel, $from_id);
    if(isset($ret->result->status) && in_array($ret->result->status, ["member","administrator","creator"])){
        sendMessage($from_id,"✅ Siz obuna bo‘ldingiz! Kino kodlarini olishingiz mumkin.");
        // Kino kodini yuborish funksiyasi shu yerda
    } else {
        $key = [
            'inline_keyboard' => [
                [['text'=>"❌ Kanalga obuna bo‘ling", 'url'=>"https://t.me/kinomandabor"]],
                [['text'=>"Obuna bo'ldim ✅", 'callback_data'=>"check"]]
            ]
        ];
        sendMessage($from_id,"❌ Siz hali kanalga obuna bo‘lmagansiz, iltimos obuna bo‘ling!", json_encode($key));
    }
}

// Start komandasi
if(isset($text) && $text == "/start"){
    if(joinchat($cid)){
        sendMessage($cid,"✅ Xush kelibsiz! Kino kodlarini ko‘rishingiz mumkin.");
    }
}

// Shu yerga sizning eski kodlaringiz qoladi: kino qo'shish, admin panel, yuborish, stat va hokazo.
?>
