const patterns = ["(^|\\.)apiproxy-device-prod-nlb-.+\\.amazonaws\\.com$", "(^|\\.)apiproxy-website-nlb-prod-.+\\.amazonaws\\.com$", "(^|\\.)dualstack\\.apiproxy-.+\\.amazonaws\\.com$", "(^|\\.)dualstack\\.ichnaea-web-.+\\.amazonaws\\.com$"];
const hostname = $request.hostname;
$done({matched: patterns.some(pattern => new RegExp(pattern).test(hostname))});
