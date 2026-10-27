/* ==========================================================================
   BITDSK LAB — 站点配置
   改这个文件就能换域名 / 仓库地址，不用动其它代码。
   ========================================================================== */
window.BITDSK_CONFIG = {
  /* 固件根地址 —— 固件已全部拆到独立仓库，本站只保留索引。
     仓库：https://github.com/bitdsk/Bitdsk_Miner_Archive

     默认指向 jsDelivr（有 CDN 缓存，国内访问更稳）。
     下面这条假设仓库根有 firmware/ 目录，里面是 n5-series/ n8-series/ 等。
     如果你的仓库根直接就是 n5-series/ 这些目录，把末尾的 /firmware 去掉。

     本地预览想看到真实文件，可临时改成：'../bitdsk-firmware/firmware' */
  firmwareBase: 'https://cdn.jsdelivr.net/gh/bitdsk/Bitdsk_Miner_Archive@main/firmware',

  /* 数据清单位置 */
  dataUrl: 'data/firmware.json',

  /* 烧录站地址（独立的 bitdsk-flash 仓库）。
     S1 / U1 / U2 的烧录包与浏览器烧录页都在那边，本站只保留索引条目。
     本站是 bitdsk.org 根域名，烧录站是 github.io 的子路径，属于跨域，
     所以这里必须用绝对地址。留空则相关按钮自动隐藏，不会产生死链。 */
  flashBase: 'https://bitdsk.github.io/bitdsk-flash/',

  /* 仓库与联系入口，页脚和导航用 */
  github: 'https://github.com/',
  repoName: 'bitdsk-site',
  email: ''
};
