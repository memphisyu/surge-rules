const patterns = [".+\\.awsdns-[0-9][0-9]\\.(co\\.uk|com|net|org)$"];
const hostname = $request.hostname;
$done({matched: patterns.some(pattern => new RegExp(pattern).test(hostname))});
