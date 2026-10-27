/* 旧 WordPress 网址 → 新页面。
   两类入口：
   1) 404.html 里按路径匹配（/bitdsk-miner-management-tools-on-pc 这种）；
   2) 首页按 ?p=123 匹配（WP 的老短链）。
   全部用站根绝对路径，bitdsk.org 和 bitdsk.github.io 都能用。 */
(function () {
  var GUIDES = '/guides/';

  var pages = {
    /* 页面 */
    'bitdsk-miner-management-tools-on-pc': '/docs/miner-tools.html',
    'miner-tools': '/docs/miner-tools.html',
    'version-comparison': '/docs/version-comparison.html',
    'api': '/docs/api.html',
    'docs': '/docs/docs.html',
    'firmware': '/firmware.html',
    'flash': '/flash.html',

    /* 保留的教程（slug 与原站一致） */
    'bitdsk-u-series-ui-design-guidelines': GUIDES + 'bitdsk-u-series-ui-design-guidelines.html',
    'blackbox-1-3-7-firmware-for-n8': GUIDES + 'blackbox-1-3-7-firmware-for-n8.html',
    'how-to-fix-the-problem-that-the-version-number-all_3-0-9_4-cannot-connect-to-the-hotspot':
      GUIDES + 'how-to-fix-the-problem-that-the-version-number-all_3-0-9_4-cannot-connect-to-the-hotspot.html',
    'solution-for-fixing-inability-to-access-the-backend-due-to-incorrect-static-ip-configuration':
      GUIDES + 'solution-for-fixing-inability-to-access-the-backend-due-to-incorrect-static-ip-configuration.html',
    'how-to-change-the-running-frequency-of-bitdsk': GUIDES + 'how-to-change-the-running-frequency-of-bitdsk.html',
    'how-to-use-redir-for-mining-pool-forwardingno-pumping': GUIDES + 'how-to-use-redir-for-mining-pool-forwardingno-pumping.html',
    'how-to-install-an-antenna': GUIDES + 'how-to-install-an-antenna.html',
    'reprint8-reasons-to-turn-down-the-transmit-power-of-your-wi-fi': GUIDES + 'reprint8-reasons-to-turn-down-the-transmit-power-of-your-wi-fi.html',
    'bitcoin-address-generation-algorithm': GUIDES + 'bitcoin-address-generation-algorithm.html',
    'esp32-antenna-install-cn': GUIDES + 'esp32-antenna-install-cn.html',
    'redir-pool-forwarding-cn': GUIDES + 'redir-pool-forwarding-cn.html',
    'esp32如何安装天线？': GUIDES + 'esp32-antenna-install-cn.html',
    '如何使用redir进行矿池转发？无抽水': GUIDES + 'redir-pool-forwarding-cn.html',

    /* 没搬过来的新闻 / 商品页 → 落到最相关的资源页 */
    'bitdsk-u1-touch-launch': '/firmware.html#u-series',
    'bitdsk-u2-touch-launch': '/firmware.html#u-series',
    'bit-horizon': '/firmware.html#u-series',
    'violetpulse': '/firmware.html#u-series',
    'bitdsk-d9': '/firmware.html#legacy',
    'bitdsk-q2': '/firmware.html#legacy',
    'bitdsk-n5-lite': '/firmware.html#legacy',
    'bitdsk-d11': '/firmware.html#legacy',
    'we-successfully-changed-the-website-server': '/'
  };

  /* ?p=123 老固定链接 */
  var posts = {
    '1454': GUIDES + 'bitdsk-u-series-ui-design-guidelines.html',
    '1272': GUIDES + 'blackbox-1-3-7-firmware-for-n8.html',
    '984': GUIDES + 'how-to-fix-the-problem-that-the-version-number-all_3-0-9_4-cannot-connect-to-the-hotspot.html',
    '810': GUIDES + 'solution-for-fixing-inability-to-access-the-backend-due-to-incorrect-static-ip-configuration.html',
    '717': GUIDES + 'how-to-change-the-running-frequency-of-bitdsk.html',
    '605': GUIDES + 'esp32-antenna-install-cn.html',
    '602': GUIDES + 'redir-pool-forwarding-cn.html',
    '591': GUIDES + 'how-to-use-redir-for-mining-pool-forwardingno-pumping.html',
    '580': GUIDES + 'reprint8-reasons-to-turn-down-the-transmit-power-of-your-wi-fi.html',
    '575': GUIDES + 'how-to-install-an-antenna.html',
    '283': GUIDES + 'bitcoin-address-generation-algorithm.html'
  };

  var key = '';
  try {
    key = decodeURIComponent(location.pathname).replace(/\/+$/, '').split('/').pop() || '';
  } catch (e) {}
  key = key.replace(/\.html?$/i, '').toLowerCase();

  var id = '';
  try {
    id = new URLSearchParams(location.search).get('p') || '';
  } catch (e) {}

  var dest = pages[key] || posts[id];
  if (!dest) return;
  /* 目标就是当前页时不要再跳，否则会自己套自己 */
  if (dest.split('#')[0] === location.pathname) return;
  location.replace(dest + (location.hash || ''));
})();
