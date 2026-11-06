const patterns = ["^chatgpt-async-webps-prod-\\s+-\\d+\\.webpubsub\\.azure\\.com$"];
const hostname = $request.hostname;
$done({matched: patterns.some(pattern => new RegExp(pattern).test(hostname))});
