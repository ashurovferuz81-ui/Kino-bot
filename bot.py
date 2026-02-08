<?php
// ================== CONFIG ==================
define('API_KEY','8501918863:AAE6YCS4j3z0JM9RcpmNXVtk2Kh1qUfABRQ');
$admin = '5775388579'; // Sizning Telegram ID
$owners = [$admin];

// ================== BOT FUNCTIONS ==================
function bot($method,$datas=[]){
    $url = "https://api.telegram.org/bot". API_KEY ."/". $method;
    $ch = curl_init();
    curl_setopt($ch,CURLOPT_URL,$url);
    curl_setopt($ch,CURLOPT_RETURNTRANSFER,true);
    curl_setopt($ch,CURLOPT_POSTFIELDS,$datas);
    $res = curl_exec($ch);
    if(curl_error($ch)) var_dump(curl_error($ch));
    return json_decode($res);
}

function sendMessage($id, $text, $key=null){
    return bot('sendMessage',[
        'chat_id'=>$id,
        'text'=>$text,
        'parse_mode'=>'html',
        'disable_web_page_preview'=>true,
        'reply_markup'=>$key
    ]);
}

function getChatMember($cid, $uid){
    return bot('getChatMember', ['chat_id'=>$cid,'user_id'=>$uid]);
}

// ================== UTILS ==================
function replyKeyboard($key){ return json_encode(['keyboard'=>$key,'resize_keyboard'=>true]); }
function removeKeyboard(){ return json_encode(['remove_keyboard'=>true]); }

// ================== TIME ==================
date_default_timezone_set('Asia/Tashkent');
$soat = date('H:i'); 
$sana = date("d.m.Y");

// ================== UPDATE ==================
$update = json_decode(file_get_contents('php://input'));
$message = $update->message ?? null;
$callback = $update->callback_query ?? null;

$cid = $message->chat->id ?? $callback->message->chat->id ?? null;
$text = $message->text ?? null;
$data = $callback->data ?? null;
$from_id = $message->from->id ?? $callback->from->id ?? null;

// ================== JOIN CHECK ==================
function joinchat($id){
    $channel = "@kinomandabor"; // Kanalni o'zgartiring
    $key = [
        'inline_keyboard'=>[
            [['text'=>"❌ Kanalga obuna bo‘ling",'url'=>"https://t.me/kinomandabor"]],
            [['text'=>"Obuna bo'ldim ✅",'callback_data'=>"check"]]
        ]
    ];
    $status = getChatMember($channel,$id)->result->status ?? "left";
    if(in_array($status,["member","administrator","creator"])) return true;
    sendMessage($id,"❌ <b>Botdan foydalanish uchun kanalga obuna bo'ling!</b>", json_encode($key));
    return false;
}

// ================== CALLBACK: CHECK ==================
if($data=="check"){
    if(joinchat($from_id)) sendMessage($from_id,"✅ Siz obuna bo‘ldingiz! Kino kodlarini olishingiz mumkin.");
}

// ================== /START ==================
if($text=="/start"){
    if(joinchat($cid)) sendMessage($cid,"✅ Xush kelibsiz! Kino kodlarini ko‘rishingiz mumkin.");
}

// ================== ADMIN PANEL ==================
$panel = replyKeyboard([
    [['text'=>"📊 Statistika"],['text'=>"🔍 Searching"]],
    [['text'=>"🎬 Kino qo'shish"],['text'=>"🗑️ Kino o'chirish"]],
    [['text'=>"👨‍💼 Adminlar"],['text'=>"📢 Kanallar"]]
]);

if(in_array($cid, [$admin]) && in_array($text, ["/panel","/admin"])){
    sendMessage($cid,"👨🏻‍💻 Boshqaruv paneliga xush kelibsiz.", $panel);
}

// ================== KINO QO‘SHISH ==================
// Bu yerga kino / video / photo qo‘shish logikasi yozish mumkin
// Faqat array yoki fayl orqali saqlash mumkin (DB ishlatilmaydi)

$kino_list = []; // DB o'rniga array

if($text=="🎬 Kino qo'shish" && $cid==$admin){
    sendMessage($cid,"📥 Iltimos, kino nomini yuboring:");
    $step[$cid] = "kino_name";
}

if(isset($step[$cid]) && $step[$cid]=="kino_name" && !empty($text)){
    $kino_list[] = ['name'=>$text,'date'=>$sana];
    sendMessage($cid,"✅ Kino qo'shildi: <b>$text</b>");
    unset($step[$cid]);
}

?>
