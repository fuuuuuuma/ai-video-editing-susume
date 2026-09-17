const CHANNELS = [
  {
    id: "susume",
    name: "AI動画編集のすゝめ",
    short: "すゝめ",
    href: "channels/susume.html",
    color: "#d92d86",
    fallback: "す",
    icon: "https://yt3.googleusercontent.com/9xet3JUseilkc7tqD-_00hHpt3668vKP5-DAHMB7ej8v-36BSuve2G7wylYsc08uUogQ72qD8eg=s900-c-k-c0x00ffffff-no-rj"
  },
  {
    id: "lab",
    name: "AI収益化ラボ",
    short: "収益化",
    href: "channels/lab.html",
    color: "#7f19c6",
    fallback: "収",
    icon: "https://yt3.googleusercontent.com/nRq-bPkCfmj6QOKkVq3jfkCC8uquD05NGS5OKJ42OXbzyfOufIsSE-tGHaxWt0NaDfd91jMtIg=s900-c-k-c0x00ffffff-no-rj"
  },
  {
    id: "ccaa",
    name: "AA／CC",
    short: "AA／CC",
    href: "channels/ccaa.html",
    color: "#0d3a66",
    fallback: "CC",
    icon: "https://yt3.googleusercontent.com/RqA6T7MQYdr0bJTstKVUA-8ODswsmAYAG3jZbWyfTwX83vl-fGuFaZeeKfSbjTFYID2BZLUQ=s900-c-k-c0x00ffffff-no-rj"
  },
  {
    id: "instagram",
    name: "Instagram奥山",
    short: "奥山",
    href: "channels/instagram.html",
    color: "#e33b32",
    fallback: "奥",
    icon: "https://scontent-nrt1-1.cdninstagram.com/v/t51.2885-19/432001402_751181006972562_3380226484654849194_n.jpg?stp=dst-jpg_s100x100_tt6&_nc_cat=109&ccb=7-5&_nc_sid=bf7eb4&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLnd3dy40MDAuQzMifQ%3D%3D&_nc_ohc=rvFcZRwAG10Q7kNvwEiV4Xl&_nc_oc=Adpe5OmTtKFsFC_Xg8l25Q0HjJpsdaxvWAXAXgDgja0QL_Zw-JxsyJhdwM9xLCrb-PE&_nc_zt=24&_nc_ht=scontent-nrt1-1.cdninstagram.com&_nc_ss=7260f&oh=00_AQLnGF7cvx8UNjqwuhDsACr34HD5Gb_8AH5melBDWJhmhA&oe=6AB1207A"
  }
];

function prefixPath(path) {
  const base = document.body.dataset.base || ".";
  return `${base}/${path}`;
}

function avatar(channel, extraClass = "") {
  return `<span class="avatar-shell ${extraClass}" style="--channel-color:${channel.color}"><span aria-hidden="true">${channel.fallback}</span><img src="${channel.icon}" alt="" loading="lazy" referrerpolicy="no-referrer"></span>`;
}

function buildRail() {
  const target = document.querySelector("[data-site-nav]");
  if (!target) return;
  const current = document.body.dataset.channel;
  target.className = "channel-rail";
  target.innerHTML = `
    <div class="rail-inner">
      <a class="rail-home" href="${prefixPath("index.html")}" aria-label="トップへ">
        <img src="${prefixPath("assets/plugin-mark.svg")}" alt="">
      </a>
      <ul class="rail-list">
        ${CHANNELS.map(channel => `
          <li><a class="rail-link" href="${prefixPath(channel.href)}" ${current === channel.id ? 'aria-current="page"' : ""}>
            ${avatar(channel)}<span>${channel.short}</span>
          </a></li>`).join("")}
        <li><a class="rail-link" href="${prefixPath("channels/other.html")}" ${current === "other" ? 'aria-current="page"' : ""}>
          <span class="avatar-shell" style="--channel-color:#39465c"><span aria-hidden="true">10</span></span><span>その他</span>
        </a></li>
      </ul>
    </div>`;
  target.querySelectorAll("img").forEach(image => {
    image.addEventListener("error", () => image.classList.add("is-broken"));
  });
}

function buildFooter() {
  const target = document.querySelector("[data-site-footer]");
  if (!target) return;
  target.className = "footer";
  target.innerHTML = `<div class="footer-inner">
    <div>AI動画編集のすゝめ — Codex Plugin</div>
    <nav aria-label="フッター">
      <a href="${prefixPath("status.html")}">検証状態</a>
      <a href="${prefixPath("privacy.html")}">プライバシー</a>
      <a href="${prefixPath("terms.html")}">利用条件</a>
      <a href="https://github.com/fuuuuuuma/ai-video-editing-susume">GitHub</a>
    </nav>
  </div>`;
}

function hydratePageAvatars() {
  document.querySelectorAll("[data-channel-avatar]").forEach(target => {
    const channel = CHANNELS.find(item => item.id === target.dataset.channelAvatar);
    if (!channel || target.querySelector("img")) return;
    target.style.setProperty("--channel-color", channel.color);
    const image = document.createElement("img");
    image.src = channel.icon;
    image.alt = "";
    image.referrerPolicy = "no-referrer";
    image.addEventListener("error", () => image.classList.add("is-broken"));
    target.appendChild(image);
  });
}

function bindCopyButtons() {
  document.querySelectorAll("[data-copy]").forEach(button => {
    button.addEventListener("click", async () => {
      const selector = button.getAttribute("data-copy");
      const source = document.querySelector(selector);
      if (!source) return;
      try {
        await navigator.clipboard.writeText(source.textContent.trim());
        const previous = button.textContent;
        button.textContent = "コピー済み";
        setTimeout(() => { button.textContent = previous; }, 1600);
      } catch {
        button.textContent = "選択してコピー";
      }
    });
  });
}

buildRail();
buildFooter();
hydratePageAvatars();
bindCopyButtons();
