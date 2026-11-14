// BARómetro: componente de la portada (buscador grande, ejemplos y «Usar mi ubicación») y de
// la barra fija del resultado (logotipo, campo con la dirección analizada, vistas e índice de
// secciones). Se monta con st.components.v2 desde app/app.py, sin iframe.
//
// En la barra, el campo enseña la dirección analizada y se edita directamente: al pulsarlo
// se selecciona el texto, al escribir salen las sugerencias y se busca al elegir una, con
// Intro o con el botón. Si se sale sin buscar (Escape o un clic fuera), vuelve la dirección.
//
// El navegador NO llama a CartoCiudad: manda al servidor lo que se escribe (con espera entre
// pulsaciones y un mínimo de letras) y el servidor devuelve las sugerencias ya filtradas
// (src/direcciones.py). Aquí no se guarda nada: ni lo escrito ni la ubicación.

const ESPERA_MS = 350;

const ICONO = {
  lupa: '<circle cx="11" cy="11" r="6.5"/><path d="M16 16l4.5 4.5"/>',
  pin: '<path d="M12 21s-6.5-5.6-6.5-11a6.5 6.5 0 0 1 13 0c0 5.4-6.5 11-6.5 11z"/><circle cx="12" cy="10" r="2.3"/>',
  mira: '<circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="1.5"/><path d="M12 2.5v3M12 18.5v3M2.5 12h3M18.5 12h3"/>',
  lista: '<path d="M5 7h14M5 12h14M5 17h14"/>',
};
const ico = (n) => `<span class="ico"><svg viewBox="0 0 24 24">${ICONO[n]}</svg></span>`;

function crear(etiqueta, clase, html) {
  const e = document.createElement(etiqueta);
  if (clase) e.className = clase;
  if (html !== undefined) e.innerHTML = html;
  return e;
}

function desplazar(id) {
  const el = document.getElementById(id);
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
  return !!el;
}

// Lleva a una sección que puede no estar todavía en la página (se está cambiando de vista).
function desplazarCuandoEste(id) {
  let intentos = 0;
  const ir = () => { if (!desplazar(id) && intentos++ < 40) setTimeout(ir, 150); };
  setTimeout(ir, 250);
}

// Enlaces de la portada a secciones de la misma página (#como-funciona, #fuentes) y enlace
// «Fuentes y licencias» del pie: si la sección está en la página, se va a ella; si no (en el
// Resumen o con una dirección sin confirmar), se le pide al servidor la vista que la tiene.
// «Planes» (portada, pie, etiquetas «Plan …» del resultado) es una página aparte: se le pide
// al componente que haya, sea la barra o el buscador de la portada, sin recargar la página.
if (!window.__bmEnlaces) {
  window.__bmEnlaces = true;
  document.addEventListener("click", (ev) => {
    const a = ev.target.closest && ev.target.closest(
      '.pt-nav a[href^="#"], .pie-bm a[href^="#"], a.plan-etq, .planes-me a[href^="#"]');
    if (!a) return;
    ev.preventDefault();
    const id = a.getAttribute("href").slice(1);
    if (desplazar(id)) return;
    const barra = document.querySelector(".bm.bm-barra") ||
      (a.dataset.ir === "planes" ? document.querySelector(".bm") : null);
    if (a.dataset.ir && barra && barra._api) {
      if (a.dataset.ir !== "planes") window.__bmIrA = id;   // «Planes» se abre arriba del todo
      barra._api.setTriggerValue(a.dataset.ir, true);
    }
  });
}

function campoHTML(d, enBarra) {
  return (
    ico(enBarra ? "pin" : "lupa") +
    `<input type="text" autocomplete="off" autocapitalize="off" spellcheck="false" enterkeyhint="search"
        role="combobox" aria-autocomplete="list" aria-expanded="false"
        aria-label="${enBarra ? "Dirección analizada. Escribe otra para cambiarla" : "Dirección del local"}"
        placeholder="${window.innerWidth < 480 ? d.placeholder_corto : d.placeholder}">` +
    (enBarra
      ? `<button type="button" class="bm-ir" aria-label="Buscar">${ico("lupa")}<span>Buscar</span></button>`
      : '<button type="button" class="bm-ir">Buscar</button>') +
    '<div class="bm-lista" role="listbox" hidden></div>'
  );
}

function construir(d) {
  const raiz = crear("div", "bm");
  if (d.modo === "portada") {
    raiz.classList.add("bm-portada");
    raiz.innerHTML =
      `<div class="bm-campo">${campoHTML(d, false)}</div>` +
      '<div class="bm-msg" role="status" hidden></div>' +
      '<div class="bm-bajo"><span>Prueba con:</span></div>' +
      '<div class="bm-priv"></div>';
    const bajo = raiz.querySelector(".bm-bajo");
    d.ejemplos.forEach((nombre) => {
      const b = crear("button", "bm-chip");
      b.type = "button";
      b.textContent = nombre;
      b.addEventListener("click", () => raiz._api.setTriggerValue("ejemplo", nombre));
      bajo.appendChild(b);
    });
    const ubi = crear("button", "bm-chip bm-ubi", ico("mira") + "Usar mi ubicación");
    ubi.type = "button";
    ubi.addEventListener("click", () => ubicar(raiz, ubi));
    bajo.appendChild(ubi);
    raiz.querySelector(".bm-priv").innerHTML = d.privacidad;
  } else {
    raiz.classList.add("bm-barra");
    raiz.innerHTML =
      '<header class="bm-top">' +
      `<button type="button" class="bm-logo" title="Volver al inicio" aria-label="BARómetro: volver al inicio">${d.logo}<b>BARómetro</b></button>` +
      `<div class="bm-campo">${campoHTML(d, true)}</div>` +
      '<div class="bm-fila2"><nav class="bm-vistas" aria-label="Vista"></nav>' +
      `<div class="bm-menu"><button type="button" aria-expanded="false">${ico("lista")}Secciones</button>` +
      '<div class="bm-menu-lista" hidden></div></div></div>' +
      "</header>" +
      '<nav class="bm-indice" aria-label="Secciones del informe"></nav>';
    raiz.querySelector(".bm-logo").addEventListener("click", () =>
      raiz._api.setTriggerValue("inicio", true));
    const menu = raiz.querySelector(".bm-menu");
    menu.firstElementChild.addEventListener("click", () => {
      const lista = menu.querySelector(".bm-menu-lista");
      lista.hidden = !lista.hidden;
      menu.firstElementChild.setAttribute("aria-expanded", String(!lista.hidden));
    });
    // Sección activa del índice según el desplazamiento.
    const alDesplazar = () => marcarSeccion(raiz);
    document.addEventListener("scroll", alDesplazar, true);
    raiz._quitar = () => document.removeEventListener("scroll", alDesplazar, true);
  }

  const input = raiz.querySelector("input");
  const lista = raiz.querySelector(".bm-lista");
  const enBarra = d.modo === "barra";
  const campo = raiz.querySelector(".bm-campo");
  raiz._s = { abierto: false, activa: 0, reloj: null, irN: null, enviando: false,
              editado: false, msgVisto: "" };

  input.addEventListener("input", () => {
    const s = raiz._s;
    s.abierto = true;
    s.editado = true;
    s.msg = "";
    s.msgVisto = raiz._d.mensaje || "";
    s.activa = 0;
    clearTimeout(s.reloj);
    const texto = input.value.trim();
    if (texto.length >= raiz._d.minimo) {
      s.reloj = setTimeout(() => raiz._api.setStateValue("q", texto), ESPERA_MS);
    }
    pintar(raiz);
  });
  input.addEventListener("focus", () => {
    raiz._s.abierto = true;
    // En la barra, al entrar se selecciona la dirección: lo que se escriba la sustituye.
    if (enBarra && !raiz._s.editado) input.select();
    pintar(raiz);
  });
  // Salir del campo con el teclado (tabulador) sin buscar: vuelve la dirección analizada.
  campo.addEventListener("focusout", (ev) => {
    if (enBarra && !campo.contains(ev.relatedTarget)) restaurar(raiz);
  });
  input.addEventListener("keydown", (ev) => {
    const s = raiz._s;
    const n = lista.querySelectorAll(".bm-op").length;
    if (ev.key === "ArrowDown" && n) { s.activa = (s.activa + 1) % n; ev.preventDefault(); pintar(raiz); }
    else if (ev.key === "ArrowUp" && n) { s.activa = (s.activa + n - 1) % n; ev.preventDefault(); pintar(raiz); }
    else if (ev.key === "Enter") { ev.preventDefault(); buscarOElegir(raiz); }
    else if (ev.key === "Escape") {
      s.abierto = false;
      if (enBarra) { restaurar(raiz); input.blur(); } else pintar(raiz);
    }
  });
  const ir = raiz.querySelector(".bm-ir");
  if (ir) {
    // El botón no debe quitar el foco del campo (en la barra, eso desharía lo escrito).
    ir.addEventListener("mousedown", (ev) => ev.preventDefault());
    ir.addEventListener("click", () => { input.focus(); buscarOElegir(raiz); });
  }
  // Un clic en una sugerencia no debe quitar el foco del campo antes de elegir.
  lista.addEventListener("mousedown", (ev) => ev.preventDefault());
  document.addEventListener("click", (ev) => {
    if (!raiz.isConnected) return;
    if (!campo.contains(ev.target)) {
      raiz._s.abierto = false;
      if (enBarra) restaurar(raiz); else pintar(raiz);
    }
    const menu = raiz.querySelector(".bm-menu");
    if (menu && !menu.contains(ev.target)) menu.querySelector(".bm-menu-lista").hidden = true;
  });
  return raiz;
}

// Barra: deja el campo como estaba, con la dirección analizada (si no se está enviando).
function restaurar(raiz) {
  const s = raiz._s;
  if (s.enviando) return;
  clearTimeout(s.reloj);
  s.editado = false;
  s.abierto = false;
  s.msg = "";
  s.msgVisto = raiz._d.mensaje || "";   // el aviso, si lo había, se da por leído
  pintar(raiz);
}

function buscarOElegir(raiz) {
  const s = raiz._s, d = raiz._d;
  const input = raiz.querySelector("input");
  const texto = input.value.trim();
  // Barra sin tocar: el botón solo lleva al campo, con la dirección seleccionada.
  if (d.modo === "barra" && !s.editado) { input.select(); return; }
  if (texto.length < d.minimo) { s.abierto = true; pintar(raiz); return; }
  if (d.q === texto && d.sugerencias.length) { elegir(raiz, s.activa); return; }
  if (d.q !== texto) {            // sin esperar: se pide ya
    clearTimeout(s.reloj);
    raiz._api.setStateValue("q", texto);
  }
  s.abierto = true;
  pintar(raiz);
}

function elegir(raiz, i) {
  const s = raiz._s, d = raiz._d;
  if (s.enviando || !d.sugerencias[i]) return;
  s.enviando = true;
  s.abierto = false;
  raiz.querySelector("input").value = d.sugerencias[i].t;
  pintar(raiz);
  raiz._api.setTriggerValue("elegida", { q: d.q, i });
}

function ubicar(raiz, boton) {
  const aviso = (t) => { raiz._s.msg = t; boton.classList.remove("cargando"); pintar(raiz); };
  if (!navigator.geolocation) {
    aviso("Tu navegador no nos deja saber dónde estás. Escribe la dirección.");
    return;
  }
  boton.classList.add("cargando");
  navigator.geolocation.getCurrentPosition(
    (p) => raiz._api.setTriggerValue("ubicacion", { lat: p.coords.latitude, lon: p.coords.longitude }),
    (e) => aviso(e.code === 1
      ? "No has dado permiso para usar tu ubicación. Escribe la dirección."
      : "No hemos podido saber dónde estás. Escribe la dirección."),
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
}

function marcarSeccion(raiz) {
  const d = raiz._d;
  if (!d || !d.secciones || !d.secciones.length) return;
  let activa = d.secciones[0].id;
  for (const s of d.secciones) {
    const el = document.getElementById(s.id);
    if (el && el.getBoundingClientRect().top < 150) activa = s.id;
  }
  raiz.querySelectorAll("[data-sec]").forEach((b) =>
    b.classList.toggle("activa", b.dataset.sec === activa));
}

function pintar(raiz) {
  const d = raiz._d, s = raiz._s;
  const input = raiz.querySelector("input");
  const lista = raiz.querySelector(".bm-lista");
  const enBarra = d.modo === "barra";
  // Barra: mientras no se escribe, el campo enseña la dirección analizada.
  if (enBarra && !s.editado && !s.enviando && input.value !== d.direccion) {
    const dentro = document.activeElement === input;
    input.value = d.direccion;
    if (dentro) input.select();
  }
  if (enBarra) input.title = d.direccion;
  const texto = input.value.trim();
  const aviso = s.msg || (d.mensaje !== s.msgVisto ? d.mensaje : "") || "";

  // ---- lista de sugerencias (en la barra, también el sitio de los avisos)
  lista.innerHTML = "";
  let visible = s.abierto && texto.length > 0 && !s.enviando && (!enBarra || s.editado);
  if (enBarra && aviso && !visible) {
    lista.appendChild(crear("div", "bm-nota bm-nota-aviso", ""));
    lista.lastChild.textContent = aviso;
    visible = true;
  } else if (visible && texto.length < d.minimo) {
    lista.appendChild(crear("div", "bm-nota", "Sigue escribiendo: calle, número y municipio."));
  } else if (visible && d.q !== texto) {
    lista.appendChild(crear("div", "bm-nota",
      'Buscando direcciones<span class="bm-puntos"><i></i><i></i><i></i></span>'));
  } else if (visible && d.estado === "error") {
    lista.appendChild(crear("div", "bm-nota",
      "Ahora no podemos buscar direcciones. Prueba más tarde."));
  } else if (visible && !d.sugerencias.length) {
    lista.appendChild(crear("div", "bm-nota",
      "No encontramos esa dirección en Madrid. Prueba a escribirla de otra forma."));
  } else if (visible) {
    s.activa = Math.min(s.activa, d.sugerencias.length - 1);
    d.sugerencias.forEach((sug, i) => {
      const b = crear("button", "bm-op" + (i === s.activa ? " activa" : ""), ico("pin"));
      b.type = "button";
      b.setAttribute("role", "option");
      b.setAttribute("aria-selected", String(i === s.activa));
      const caja = crear("span");
      caja.appendChild(document.createTextNode(sug.t));
      if (sug.nota) { const n = crear("small"); n.textContent = sug.nota; caja.appendChild(n); }
      b.appendChild(caja);
      b.addEventListener("click", () => elegir(raiz, i));
      lista.appendChild(b);
    });
  }
  lista.hidden = !visible;
  input.setAttribute("aria-expanded", String(visible));

  // ---- mensajes (portada: bajo el buscador)
  const msg = raiz.querySelector(".bm-msg");
  if (msg) {
    msg.textContent = aviso;
    msg.hidden = !aviso;
  }

  if (!enBarra) return;
  // ---- barra del resultado
  const vistas = raiz.querySelector(".bm-vistas");
  vistas.innerHTML = "";
  vistas.parentElement.style.display = d.vistas.length ? "" : "none";
  d.vistas.forEach((v) => {
    const b = crear("button", v === d.vista ? "activa" : "");
    b.type = "button";
    b.textContent = v;
    b.setAttribute("aria-pressed", String(v === d.vista));
    b.addEventListener("click", () => {
      if (v !== raiz._d.vista) raiz._api.setTriggerValue("vista", v);
    });
    vistas.appendChild(b);
  });
  raiz.classList.toggle("con-indice", d.secciones.length > 0);
  const indice = raiz.querySelector(".bm-indice");
  const menu = raiz.querySelector(".bm-menu-lista");
  indice.innerHTML = d.secciones.length ? "<b>En este informe</b>" : "";
  menu.innerHTML = "";
  d.secciones.forEach((sec) => {
    [indice, menu].forEach((donde) => {
      const b = crear("button");
      b.type = "button";
      b.dataset.sec = sec.id;
      b.textContent = sec.t;
      b.addEventListener("click", () => { menu.hidden = true; desplazar(sec.id); });
      donde.appendChild(b);
    });
  });
  marcarSeccion(raiz);
}

export default function (componente) {
  const { data, parentElement, setStateValue, setTriggerValue } = componente;
  let raiz = parentElement.querySelector(".bm");
  if (!raiz) {
    raiz = construir(data);
    parentElement.appendChild(raiz);
    raiz._subir = true;
  }
  raiz._api = { setStateValue, setTriggerValue };
  raiz._d = data;
  if (window.__bmIrA) {            // sección pedida desde el pie, en otra vista
    desplazarCuandoEste(window.__bmIrA);
    window.__bmIrA = null;
  }
  // Si el servidor contesta con un aviso (no se pudo situar la dirección), se puede volver a
  // buscar: el campo deja de estar «enviando».
  if (data.mensaje && data.mensaje !== raiz._s.msgVisto) {
    raiz._s.enviando = false;
    raiz._s.editado = false;
  }
  pintar(raiz);

  if (data.modo === "barra") {
    // Al cambiar de vista o de dirección se vuelve arriba; «ir_a» lleva a una sección.
    const marca = data.vista + "|" + data.direccion;
    const principal = document.querySelector('[data-testid="stMain"]');
    if (raiz._marca !== marca) {
      raiz._marca = marca;
      if (principal && !(data.ir_a && data.ir_a.n !== raiz._s.irN)) principal.scrollTo({ top: 0 });
    }
    if (data.ir_a && data.ir_a.n !== raiz._s.irN) {
      raiz._s.irN = data.ir_a.n;
      let intentos = 0;
      const ir = () => { if (!desplazar(data.ir_a.id) && intentos++ < 20) setTimeout(ir, 150); };
      setTimeout(ir, 250);
    }
  }
  return () => { if (raiz._quitar && !raiz.isConnected) raiz._quitar(); };
}
