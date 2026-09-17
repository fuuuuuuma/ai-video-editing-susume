const CHANNELS = [
  {
    id: "susume",
    name: "AI動画編集のすゝめ",
    short: "すゝめ",
    href: "channels/susume.html",
    color: "#bf2b6f",
    fallback: "す",
    icon: "https://yt3.googleusercontent.com/9xet3JUseilkc7tqD-_00hHpt3668vKP5-DAHMB7ej8v-36BSuve2G7wylYsc08uUogQ72qD8eg=s900-c-k-c0x00ffffff-no-rj"
  },
  {
    id: "lab",
    name: "AI収益化ラボ",
    short: "収益化ラボ",
    href: "channels/lab.html",
    color: "#6b3ba4",
    fallback: "収",
    icon: "https://yt3.googleusercontent.com/nRq-bPkCfmj6QOKkVq3jfkCC8uquD05NGS5OKJ42OXbzyfOufIsSE-tGHaxWt0NaDfd91jMtIg=s900-c-k-c0x00ffffff-no-rj"
  },
  {
    id: "ccaa",
    name: "AA／CC",
    short: "AA／CC",
    href: "channels/ccaa.html",
    color: "#28577f",
    fallback: "CC",
    icon: "https://yt3.googleusercontent.com/RqA6T7MQYdr0bJTstKVUA-8ODswsmAYAG3jZbWyfTwX83vl-fGuFaZeeKfSbjTFYID2BZLUQ=s900-c-k-c0x00ffffff-no-rj"
  },
  {
    id: "instagram",
    name: "Instagram奥山",
    short: "奥山ショート",
    href: "channels/instagram.html",
    color: "#bd483f",
    fallback: "奥",
    icon: "https://scontent-nrt1-1.cdninstagram.com/v/t51.2885-19/432001402_751181006972562_3380226484654849194_n.jpg?stp=dst-jpg_s100x100_tt6&_nc_cat=109&ccb=7-5&_nc_sid=bf7eb4&efg=eyJ2ZW5jb2RlX3RhZyI6InByb2ZpbGVfcGljLnd3dy40MDAuQzMifQ%3D%3D&_nc_ohc=rvFcZRwAG10Q7kNvwEiV4Xl&_nc_oc=Adpe5OmTtKFsFC_Xg8l25Q0HjJpsdaxvWAXAXgDgja0QL_Zw-JxsyJhdwM9xLCrb-PE&_nc_zt=24&_nc_ht=scontent-nrt1-1.cdninstagram.com&_nc_ss=7260f&oh=00_AQLnGF7cvx8UNjqwuhDsACr34HD5Gb_8AH5melBDWJhmhA&oe=6AB1207A"
  }
];

function prefixPath(path) {
  const base = document.body.dataset.base || ".";
  return `${base}/${path}`;
}

function avatar(channel) {
  return `<span class="avatar-shell" style="--channel-color:${channel.color}"><span aria-hidden="true">${channel.fallback}</span><img src="${channel.icon}" alt="" loading="lazy" referrerpolicy="no-referrer"></span>`;
}

function attachImageFallbacks(root = document) {
  root.querySelectorAll(".avatar-shell img").forEach(image => {
    image.addEventListener("error", () => image.classList.add("is-broken"));
  });
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
          <li>
            <a class="rail-link" style="--channel-color:${channel.color}" href="${prefixPath(channel.href)}" ${current === channel.id ? 'aria-current="page"' : ""}>
              ${avatar(channel)}<span>${channel.short}</span>
            </a>
          </li>`).join("")}
        <li>
          <a class="rail-link" style="--channel-color:#28736d" href="${prefixPath("channels/other.html")}" ${current === "other" ? 'aria-current="page"' : ""}>
            <span class="avatar-shell" style="--channel-color:#28736d"><span aria-hidden="true">10</span></span><span>その他</span>
          </a>
        </li>
      </ul>
    </div>`;

  attachImageFallbacks(target);
}

function buildFooter() {
  const target = document.querySelector("[data-site-footer]");
  if (!target) return;

  target.className = "footer";
  target.innerHTML = `<div class="footer-inner">
    <div>AI動画編集のすゝめ　公開版ガイド</div>
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
    target.appendChild(image);
  });

  attachImageFallbacks();
}

function bindCopyButtons() {
  document.querySelectorAll("[data-copy]").forEach(button => {
    button.addEventListener("click", async () => {
      const source = document.querySelector(button.getAttribute("data-copy"));
      if (!source) return;

      try {
        await navigator.clipboard.writeText(source.textContent.trim());
        const original = button.textContent;
        button.textContent = "コピーしました";
        window.setTimeout(() => { button.textContent = original; }, 1600);
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
