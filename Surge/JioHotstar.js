const patterns = ["^hses[1-7]?\\.akamaized\\.net$"];
const hostname = $request.hostname;
$done({matched: patterns.some(pattern => new RegExp(pattern).test(hostname))});
