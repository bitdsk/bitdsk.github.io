/* ==========================================================================
   BITDSK LAB — 前端渲染
   数据唯一来源：data/firmware.json
   依赖：js/config.js（可选，缺省用站内路径）
   ========================================================================== */
(function () {
  'use strict';

  var CFG = window.BITDSK_CONFIG || {};
  var BASE = String(CFG.firmwareBase || '').replace(/\/+$/, '');
  var FLASH_BASE = String(CFG.flashBase || '').replace(/\/+$/, '');
  var DATA_URL = CFG.dataUrl || 'data/firmware.json';

  /* ---------------------------------------------------------- 小工具 */
  function esc(s) {
    return String(s == null ? '' : s)
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;');
  }

  /* 固件路径 → 真实 URL（支持指向独立仓库 / CDN） */
  function fileUrl(p) {
    if (!p) return '#';
    if (/^https?:\/\//.test(p)) return p;
    return BASE ? BASE + '/' + p.replace(/^firmware\//, '') : p;
  }

  /* 烧录页 URL。
     flashPage 以 '#' 开头 → 烧录包已迁到独立仓库，拼 flashBase；
     flashBase 未配置时返回 ''，调用方据此隐藏按钮，不产生死链。 */
  function flashUrl(m) {
    var p = m && m.flashPage;
    if (!p) return '';
    if (/^https?:\/\//.test(p)) return p;
    if (p.charAt(0) === '#') return FLASH_BASE ? FLASH_BASE + '/' + p : '';
    return p;
  }

  function statusPill(m) {
    var cls = { active: 'active', legacy: 'legacy', tool: 'tool' }[m.status] || 'legacy';
    return '<span class="pill ' + cls + '">' + esc(m.statusText) + '</span>';
  }

  /* ---------------------------------------------------------- 首页型号卡片 */
  function renderModelCards(root, data) {
    root.innerHTML = data.models.map(function (m) {
      var chips = (m.chips || []).slice(0, 5).map(function (c) {
        return '<span>' + esc(c) + '</span>';
      }).join('');
      var latest = m.latest
        ? '<b>' + esc(m.latest) + '</b>'
        : (m.method === 'download' ? '—' : '—');
      var go = m.id === 'tools' ? 'Open tools' : 'View firmware';
      /* 烧录包外迁的型号本地文件数为 0，别显示成 "0 files" */
      var countTxt = m.count
        ? m.count + ' files'
        : (m.flashExternal ? 'browser flash' : '0 files');
      return '' +
        '<a class="model-card" href="firmware.html#' + esc(m.id) + '">' +
          '<div class="mc-top">' +
            '<div>' +
              '<h3 class="mc-name">' + esc(m.name) + '</h3>' +
              '<div class="mc-sub">' + esc(m.title) + '</div>' +
            '</div>' +
            statusPill(m) +
          '</div>' +
          '<p class="mc-desc">' + esc(m.summary) + '</p>' +
          '<div class="mc-chips">' + chips + '</div>' +
          '<div class="mc-foot">' +
            '<span class="mc-latest">Latest ' + latest + ' · ' + countTxt + '</span>' +
            '<span class="mc-go">' + go + ' &rarr;</span>' +
          '</div>' +
        '</a>';
    }).join('');
  }

  /* ---------------------------------------------------------- 统计数字 */
  function renderStats(data) {
    var map = {
      files: data.stats.files,
      models: data.stats.models,
      size: data.stats.size,
      guides: 8
    };
    document.querySelectorAll('[data-stat]').forEach(function (el) {
      var k = el.getAttribute('data-stat');
      if (map[k] != null) el.textContent = map[k];
    });
  }

  /* ---------------------------------------------------------- 固件页 */
  function rowHtml(m, r, isLatest) {
    var tags = [];
    if (isLatest) tags.push('<span class="pill new">Latest</span>');
    if (r.important) tags.push('<span class="pill imp">Important</span>');
    if (r.status === 'abandoned') tags.push('<span class="pill dead">Abandoned</span>');
    if (r.status === 'withdrawn') tags.push('<span class="pill dead">Withdrawn</span>');
    if (r.status === 'expired') tags.push('<span class="pill dead">Expired</span>');

    var dls = (r.files || []).map(function (f) {
      var primary = isLatest && (r.files.length === 1 || f === r.files[0]);
      return '<a class="dl-btn' + (primary ? ' primary' : '') + '" href="' + esc(fileUrl(f.path)) +
        '" download title="' + esc(f.path) + '">' +
        esc(f.label) + ' <span class="sz">' + esc(f.size) + '</span></a>' +
        '<button class="sha-btn" type="button" data-sha="' + esc(f.sha256) + '" title="Copy SHA256 of ' +
        esc(f.path.split('/').pop()) + '">SHA</button>';
    }).join('');

    if (!dls && r.status === 'flash' && flashUrl(m)) {
      dls = '<a class="dl-btn primary" href="' + esc(flashUrl(m)) + '">Flash in browser</a>';
    }
    if (!dls && r.noteLink) {
      dls = '<a class="dl-btn ghost" href="' + esc(r.noteLink) + '" target="_blank" rel="noopener">Details</a>';
    }
    if (!dls) {
      var why = { withdrawn: 'Withdrawn', abandoned: 'Abandoned', expired: 'Expired' }[r.status] || 'Not published';
      dls = '<span class="dl-btn ghost" style="cursor:default;opacity:.5">' + why + '</span>';
    }

    var chg = (r.changes || []).length
      ? '<ul>' + r.changes.map(function (c) { return '<li>' + esc(c) + '</li>'; }).join('') + '</ul>'
      : '<span style="opacity:.5">—</span>';

    var dead = (r.status === 'abandoned' || r.status === 'expired' || r.status === 'withdrawn') ? ' class="dead"' : '';

    return '<tr' + dead + ' data-search="' + esc((r.version + ' ' + (r.changes || []).join(' ')).toLowerCase()) + '">' +
      '<td class="c-date">' + esc(r.date) + '</td>' +
      '<td class="c-ver"><div class="v">' + esc(r.version) + '</div>' +
        (tags.length ? '<div class="tags">' + tags.join('') + '</div>' : '') + '</td>' +
      '<td class="c-chg">' + chg + '</td>' +
      '<td class="c-dl"><div class="dls">' + dls + '</div></td>' +
    '</tr>';
  }

  function sectionHtml(m) {
    var releases = m.releases || [];
    var latestIdx = -1;
    for (var i = 0; i < releases.length; i++) {
      if (releases[i].files && releases[i].files.length) { latestIdx = i; break; }
    }
    if (latestIdx < 0) {
      for (var j = 0; j < releases.length; j++) {
        if (releases[j].status === 'flash') { latestIdx = j; break; }
      }
    }

    var rows = releases.map(function (r, idx) {
      return rowHtml(m, r, idx === latestIdx);
    }).join('');

    var specs = (m.specs || []).map(function (s) {
      return '<span>' + esc(s[0]) + '<b>' + esc(s[1]) + '</b></span>';
    }).join('');

    var meta = '';
    if (m.latest) meta += '<div class="kv">Latest<b>' + esc(m.latest) + '</b></div>';
    /* 烧录包外迁的型号本地没有可下载文件，显示 external 而不是 0 */
    var fileTxt = (m.count || 0) > 0 ? String(m.count) : (m.flashExternal ? 'external' : '0');
    meta += '<div class="kv">Files<b>' + fileTxt + '</b></div>';
    meta += '<div class="kv">Method<b>' + esc(m.methodText || '—') + '</b></div>';
    var fu = flashUrl(m);
    if (m.docPage) {
      meta += '<a class="btn btn-sm" href="' + esc(m.docPage) + '">Read guide</a>';
    }
    if (fu) {
      meta += '<a class="btn btn-sm btn-primary" href="' + esc(fu) + '"' +
        (m.flashExternal ? ' target="_blank" rel="noopener"' : '') + '>Flash tool</a>';
    }

    /* 烧录包已迁到独立仓库时的说明 */
    var extra = '';
    /* 有主版本表时，附加表格要接在下面（去掉上圆角）；没有则自成一块 */
    var contStyle = rows ? ' style="border-radius:0;border-top:none"' : '';
    if (m.flashExternal && fu) {
      extra += '<div class="notice info" style="margin:18px 0 0">' +
        '<b>Flash image is published separately.</b> ' +
        'The bootloader, partition table, NVS and application for ' + esc(m.name) +
        ' live in the <a href="' + esc(fu) + '" style="color:var(--accent)" target="_blank" rel="noopener">Bitdsk Flash Tool</a>' +
        ' repository, together with the in-browser flasher.' +
        (m.count ? ' The files listed below are the regular OTA downloads and stay on this site.' : '') +
        '</div>';
    }

    /* 烧录包 / 附加文件 */
    if (m.flashers && m.flashers.length) {
      extra += '<div class="rel-wrap"' + contStyle + '><table class="rel"><tbody>' +
        m.flashers.map(function (fl) {
          return '<tr><td class="c-date">' + esc(fl.version) + '</td>' +
            '<td class="c-ver"><div class="v">' + esc(fl.model) + '</div>' +
            '<div class="tags"><span class="pill flash">Full image</span></div></td>' +
            '<td class="c-chg">Complete bootable image — bootloader, partition table, NVS, app, OTA data (' +
            fl.parts.length + ' parts, ' + esc(fl.size) + ')</td>' +
            '<td class="c-dl"><div class="dls">' +
              '<a class="dl-btn primary" href="' + esc(fu) + '">Flash in browser</a>' +
              '<a class="dl-btn ghost" href="' + esc(fileUrl(fl.manifest)) + '" download>manifest.json</a>' +
            '</div></td></tr>';
        }).join('') + '</tbody></table></div>';
    }
    if (m.extraFiles && m.extraFiles.length) {
      extra += '<div class="rel-wrap"' + contStyle + '><table class="rel"><tbody>' +
        m.extraFiles.map(function (f) {
          return '<tr><td class="c-date">—</td>' +
            '<td class="c-ver"><div class="v">' + esc(f.label) + '</div></td>' +
            '<td class="c-chg"><span class="mono" style="font-size:12.5px">' + esc(f.path.split('/').pop()) + '</span></td>' +
            '<td class="c-dl"><div class="dls"><a class="dl-btn" href="' + esc(fileUrl(f.path)) + '" download>' +
              'Download <span class="sz">' + esc(f.size) + '</span></a></div></td></tr>';
        }).join('') + '</tbody></table></div>';
    }

    /* 没有版本行时不渲染空表（烧录包已外迁的型号就是这种情况） */
    var tableHtml = '';
    if (rows) {
      tableHtml = '<div class="rel-wrap"><table class="rel">' +
        '<thead><tr><th>Date</th><th>Version</th><th>Changes</th><th style="text-align:right">Download</th></tr></thead>' +
        '<tbody>' + rows + '</tbody>' +
      '</table></div>';
    }

    return '<section class="model-section" id="' + esc(m.id) + '" data-model="' + esc(m.id) + '">' +
      '<div class="ms-head">' +
        '<div>' +
          '<h2>' + esc(m.name) + ' ' + statusPill(m) + '</h2>' +
          '<div class="ms-title">' + esc(m.title) + '</div>' +
          '<p class="ms-desc">' + esc(m.summary) + '</p>' +
          '<div class="ms-specs">' + specs + '</div>' +
        '</div>' +
        '<div class="ms-meta">' + meta + '</div>' +
      '</div>' + tableHtml + extra +
    '</section>';
  }

  function renderFirmwarePage(data) {
    var host = document.querySelector('[data-firmware-page]');
    if (!host) return;

    var tabsEl = document.getElementById('modelTabs');
    var qEl = document.getElementById('fwq');
    var metaEl = document.getElementById('fwmeta');
    var sectionsEl = document.getElementById('fwSections');
    var emptyEl = document.getElementById('fwEmpty');

    if (tabsEl) {
      tabsEl.innerHTML = '<button class="chip active" data-filter="all">All models</button>' +
        data.models.map(function (m) {
          return '<button class="chip" data-filter="' + esc(m.id) + '">' + esc(m.name) +
            '<span class="c">' + (m.count || 0) + '</span></button>';
        }).join('');
    }

    sectionsEl.innerHTML = data.models.map(sectionHtml).join('');

    /* 附加资源（Gerber 等） */
    if (data.extras && data.extras.length) {
      sectionsEl.innerHTML += '<section class="model-section" id="hardware">' +
        '<div class="ms-head"><div><h2>Hardware files <span class="pill tool">Source</span></h2>' +
        '<div class="ms-title">PCB / Gerber</div>' +
        '<p class="ms-desc">Board fabrication files released by Bitdsk.</p></div></div>' +
        '<div class="rel-wrap"><table class="rel"><tbody>' +
        data.extras.map(function (e) {
          return '<tr><td class="c-date">—</td>' +
            '<td class="c-ver"><div class="v">' + esc(e.label) + '</div></td>' +
            '<td class="c-chg"><span class="mono" style="font-size:12.5px">' + esc(e.name) + '</span></td>' +
            '<td class="c-dl"><div class="dls"><a class="dl-btn" href="' + esc(fileUrl(e.path)) +
            '" download>Download <span class="sz">' + esc(e.size) + '</span></a></div></td></tr>';
        }).join('') + '</tbody></table></div></section>';
    }

    var filter = 'all';

    function apply() {
      var q = (qEl ? qEl.value : '').trim().toLowerCase();
      var shownRows = 0, totalRows = 0, shownSections = 0;

      sectionsEl.querySelectorAll('.model-section').forEach(function (sec) {
        var id = sec.getAttribute('data-model');
        /* 附加区块（Gerber 等）没有 data-model，只在 "All models" 下出现 */
        var isExtra = !id;
        var modelOk = (filter === 'all') || (!isExtra && id === filter);
        var secShown = 0;

        sec.querySelectorAll('tbody tr').forEach(function (tr) {
          var hay = (tr.getAttribute('data-search') || '') + ' ' + tr.textContent.toLowerCase();
          var ok = modelOk && (!q || hay.indexOf(q) !== -1);
          tr.style.display = ok ? '' : 'none';
          if (ok) { secShown++; shownRows++; }
          totalRows++;
        });

        /* 烧录包外迁的型号没有版本行，但有说明块，不能因为 0 行就整块隐藏 */
        var hasNote = !!sec.querySelector('.notice');
        var hide = secShown === 0 && !hasNote;
        if (!modelOk) hide = true;
        sec.style.display = hide ? 'none' : '';
        if (!hide) shownSections++;
      });

      if (emptyEl) emptyEl.style.display = (shownRows === 0 && shownSections === 0) ? '' : 'none';
      if (metaEl) {
        if (!q && filter === 'all') {
          metaEl.textContent = totalRows + ' entries across ' + shownSections +
            ' groups · binaries served from Bitdsk_Miner_Archive';
        } else if (shownRows === 0) {
          var fm = data.models.filter(function (m) { return m.id === filter; })[0];
          metaEl.textContent = (fm && fm.flashExternal)
            ? 'No downloads in this repository — the flash image is hosted in the Flash Tool repository'
            : 'No matching entries';
        } else {
          metaEl.textContent = 'Showing ' + shownRows + ' of ' + totalRows + ' entries';
        }
      }
    }

    if (tabsEl) {
      tabsEl.addEventListener('click', function (e) {
        var btn = e.target.closest('.chip');
        if (!btn) return;
        tabsEl.querySelectorAll('.chip').forEach(function (c) { c.classList.remove('active'); });
        btn.classList.add('active');
        filter = btn.getAttribute('data-filter');
        if (filter !== 'all') {
          var sec = document.getElementById(filter);
          if (sec) {
            window.scrollTo({ top: sec.getBoundingClientRect().top + window.scrollY - 130, behavior: 'smooth' });
          }
        }
        apply();
      });
    }
    if (qEl) qEl.addEventListener('input', apply);

    /* 复制 SHA256 */
    host.addEventListener('click', function (e) {
      var btn = e.target.closest('.sha-btn');
      if (!btn) return;
      var sha = btn.getAttribute('data-sha') || '';
      var done = function () {
        var old = btn.textContent;
        btn.textContent = 'COPIED';
        btn.classList.add('copied');
        setTimeout(function () { btn.textContent = old; btn.classList.remove('copied'); }, 1400);
      };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(sha).then(done, function () { window.prompt('SHA256', sha); });
      } else {
        window.prompt('SHA256', sha);
      }
    });

    apply();

    /* 直接带 #型号 进来时，选中对应标签 */
    var hash = (location.hash || '').replace('#', '');
    if (hash && document.getElementById(hash)) {
      var tab = tabsEl && tabsEl.querySelector('[data-filter="' + hash + '"]');
      if (tab) tab.click();
      setTimeout(function () {
        var sec = document.getElementById(hash);
        if (sec) window.scrollTo({ top: sec.getBoundingClientRect().top + window.scrollY - 130, behavior: 'smooth' });
      }, 60);
    }
  }

  /* ---------------------------------------------------------- 通用交互 */
  function ui() {
    var backtop = document.getElementById('backtop');
    if (backtop) {
      window.addEventListener('scroll', function () {
        backtop.classList.toggle('show', window.scrollY > 400);
      }, { passive: true });
    }
    /* 移动端菜单 */
    document.querySelectorAll('.hamburger').forEach(function (b) {
      b.addEventListener('click', function () {
        document.getElementById('nav').classList.toggle('open');
      });
    });
    /* 当前页高亮：页面里已手工标注 .active 时不再自动判断 */
    var nav = document.getElementById('nav');
    if (nav && !nav.querySelector('a.active')) {
      var here = location.pathname.replace(/\/+$/, '') || '/';
      if (/\/$/.test(location.pathname)) here = location.pathname + 'index.html';
      nav.querySelectorAll('a').forEach(function (a) {
        var href = a.getAttribute('href') || '';
        if (!href || /^https?:/.test(href)) return;
        var abs;
        try { abs = new URL(href, location.href).pathname; } catch (e) { return; }
        if (abs === here || abs === location.pathname) a.classList.add('active');
      });
    }
  }

  /* ---------------------------------------------------------- 启动 */
  function boot() {
    ui();
    var needData = document.querySelector('[data-model-cards],[data-firmware-page]');
    if (!needData) return;

    fetch(DATA_URL, { cache: 'no-cache' })
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) {
        var cards = document.querySelector('[data-model-cards]');
        if (cards) renderModelCards(cards, data);
        renderStats(data);
        renderFirmwarePage(data);
        var gen = document.querySelector('[data-generated]');
        if (gen && data.site) gen.textContent = data.site.generated;
      })
      .catch(function (err) {
        document.querySelectorAll('[data-model-cards],[data-firmware-page]').forEach(function (el) {
          el.innerHTML = '<div class="empty">Could not load <code>' + DATA_URL + '</code> — ' + esc(err.message) +
            '<br><br>Open the site through a local server (not file://) so the browser is allowed to fetch JSON.</div>';
        });
        console.error('[bitdsk] data load failed', err);
      });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
