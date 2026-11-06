const patterns = ["^ewcdn[0-9]+\\.nowe\\.com$"];
const hostname = $request.hostname;
$done({matched: patterns.some(pattern => new RegExp(pattern).test(hostname))});
