const els = {
  grid: document.getElementById("grid"),
  empty: document.getElementById("empty"),
  last: document.getElementById("last"),
  notice: document.getElementById("notice"),
  search: document.getElementById("search"),
  sort: document.getElementById("sort"),
};

let data = [];

async function load() {
  try {
    const res = await fetch("./data/movies.json", { cache: "no-store" });
    const json = await res.json();
    data = json.items || [];
    if ((json.count || 0) === 0) {
      els.notice.classList.remove("hidden");
    } else {
      els.notice.classList.add("hidden");
    }
    if (json.fetched_at_utc) {
      const d = new Date(json.fetched_at_utc);
      els.last.textContent = `Обновлено: ${d.toLocaleString()}`;
    } else {
      els.last.textContent = "Ожидание первой загрузки…";
    }
    render();
  } catch (e) {
    els.last.textContent = "Ошибка загрузки данных";
    console.error(e);
  }
}

function card(item) {
  const href = `movie.html?id=${item.id}`;
  const rating = typeof item.vote_average === "number" ? item.vote_average.toFixed(1) : "—";
  const genres = (item.genres || []).slice(0, 2).join(", ");
  return `
    <a href="${href}" class="group block rounded-2xl overflow-hidden bg-white border hover:shadow transition">
      <div class="relative">
        ${item.poster_url ? `
          <img src="${item.poster_url}" alt="${item.title}" loading="lazy" class="w-full aspect-[2/3] object-cover">
        ` : `
          <div class="w-full aspect-[2/3] bg-neutral-200 grid place-items-center text-neutral-500">Нет постера</div>
        `}
        <div class="absolute top-2 left-2 text-xs bg-black/70 text-white px-2 py-1 rounded-full">⭐ ${rating}</div>
      </div>
      <div class="p-3">
        <div class="font-medium leading-tight line-clamp-2 group-hover:underline">${item.title}</div>
        <div class="mt-1 text-sm text-neutral-600">${item.release_date || "—"}</div>
        <div class="mt-1 text-xs text-neutral-500 line-clamp-1">${genres}</div>
      </div>
    </a>
  `;
}

function applyFilters() {
  const q = (els.search.value || "").toLowerCase().trim();
  let arr = data.filter(x => !q || (x.title || "").toLowerCase().includes(q));
  switch (els.sort.value) {
    case "rating_desc": arr.sort((a,b)=>(b.vote_average??0)-(a.vote_average??0)); break;
    case "title_asc": arr.sort((a,b)=>(a.title||"").localeCompare(b.title||"")); break;
    case "date_desc":
    default: arr.sort((a,b)=> (b.release_date||"") > (a.release_date||"") ? 1 : -1);
  }
  return arr;
}

function render() {
  const arr = applyFilters();
  els.grid.innerHTML = arr.map(card).join("");
  els.empty.classList.toggle("hidden", arr.length !== 0);
}

["input","change"].forEach(evt=>{
  els.search.addEventListener(evt, render);
  els.sort.addEventListener(evt, render);
});

load();
