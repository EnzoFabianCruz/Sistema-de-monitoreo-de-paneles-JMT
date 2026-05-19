document.addEventListener("DOMContentLoaded", function () {
    const modoEdicion = document.querySelector("form").dataset.modo === "edicion";
    const depSelect  = document.getElementById("departamento");
    const provSelect = document.getElementById("provincia");
    const distSelect = document.getElementById("distrito");
    const zonaSelect = document.getElementById("zona");
    const tbody = document.getElementById("tabla-body");

    // =========================
    // DEPARTAMENTO
    // =========================
    document.querySelector("form").addEventListener("submit", function () {

    const filas = document.querySelectorAll("#tabla-body tr");

    filas.forEach(fila => {

        const check = fila.querySelector(".fila-check");

        if (!check.checked) {
            // desactiva inputs de esa fila
            fila.querySelectorAll("input, select").forEach(el => {
                el.disabled = true;
            });
        }
    });

});
    depSelect.addEventListener("change", async function () {

        const dep = this.value.trim();

        provSelect.innerHTML = `<option value="">Seleccione Provincia</option>`;
        distSelect.innerHTML = `<option value="">Seleccione Distrito</option>`;
        distSelect.disabled = true;

        if (!dep) return;

        try {
            const res = await fetch(`/ajax/provincias/?dep=${dep}`);
            const data = await res.json();

            data.forEach(p => {
                const opt = document.createElement("option");
                opt.value = p.CodigoProvincia.trim();
                opt.textContent = p.Nombre;
                provSelect.appendChild(opt);
            });

        } catch (error) {
            console.error("Error provincias:", error);
        }

        actualizarZona();
    });

    // =========================
    // PROVINCIA
    // =========================
    provSelect.addEventListener("change", async function () {

        const dep  = depSelect.value.trim();
        const prov = this.value.trim();

        distSelect.innerHTML = `<option value="">Seleccione Distrito</option>`;

        const esLima = (dep === "15" && prov === "01");

        if (esLima) {
            distSelect.disabled = false;

            try {
                const res = await fetch(`/ajax/distritos/?dep=${dep}&prov=${prov}`);
                const data = await res.json();

                data.forEach(d => {
                    const opt = document.createElement("option");
                    opt.value = d.CodigoDistrito.trim();
                    opt.textContent = d.Nombre;
                    distSelect.appendChild(opt);
                });

            } catch (error) {
                console.error("Error distritos:", error);
            }

        } else {
            distSelect.disabled = true;

            // 🔥 cargar tabla directo si NO es Lima
            cargarUbicaciones(dep, prov, null);
        }

        actualizarZona();
    });

    // =========================
    // DISTRITO
    // =========================
    distSelect.addEventListener("change", function () {

        const dep  = depSelect.value.trim();
        const prov = provSelect.value.trim();
        const dist = this.value.trim();

        if (dep === "15" && prov === "01") {
            cargarUbicaciones(dep, prov, dist);
        }
    });

    // =========================
    // ZONA AUTOMATICA
    // =========================
    function actualizarZona() {

        const dep  = depSelect.value.trim();
        const prov = provSelect.value.trim();

        if (!dep || !prov) {
            zonaSelect.value = "";
            return;
        }

        zonaSelect.value = (dep === "15" && prov === "01") ? "L" : "P";
    }
    function renumerarFilas() {
    const filas = tbody.querySelectorAll("tr");

    filas.forEach((fila, index) => {
        // Validamos que la fila tenga al menos 2 columnas antes de numerar
        if (fila.children && fila.children.length > 1) {
            fila.children[1].textContent = index + 1;
        }
    });
}

    // =========================
    // CARGAR UBICACIONES
    // =========================
    function cargarUbicaciones(dep, prov, dist) {

        let url = `/ajax/ubicaciones/?dep=${dep}&prov=${prov}`;

        if (dist) {
            url += `&dist=${dist}`;
        }

        fetch(url)
            .then(res => res.json())
            .then(data => {
                cargarTabla(data, modoEdicion);;
            })
            .catch(err => console.error("Error ubicaciones:", err));
    }
function ordenarMarcados() {

        const filas = Array.from(tbody.querySelectorAll("tr"));

        filas.sort((a, b) => {
            const aCheck = a.querySelector(".fila-check")?.checked ? 1 : 0;
            const bCheck = b.querySelector(".fila-check")?.checked ? 1 : 0;
            return bCheck - aCheck;
        });

        tbody.innerHTML = "";
        filas.forEach(f => tbody.appendChild(f));
    }
function cargarTabla(data) {
    const tbody = document.getElementById("tabla-body");
    const seleccionados = new Set();
    const mapaTipos = {
        "01": "TORRE", "03": "OTRO", "04": "BANDEROLA", "06": "BANNER",
        "07": "CAJA LUMINOSA", "08": "LOGO CHICO", "09": "LOGO GRANDE",
        "10": "LUCES LED", "11": "MINIBANDEROLAS", "12": "MINIPOLAR",
        "13": "PANEL", "14": "PANEL CARRETERO", "15": "PANEL MONUMENTAL",
        "16": "PANEL PUBLICITARIO", "17": "PANEL VERTICAL", "18": "PANELETA",
        "20": "PARCHE", "23": "PORTICO", "24": "POSTE BANDERA",
        "25": "POSTE EN L", "26": "SEÑALETICAS", "27": "TORRE UNIPOLAR",
        "28": "VINIL", "29": "VALLAS ALTAS", "30": "TORRE MINIPOLAR",
        "31": "MEGAVALLA", "32": "TORRE TRIPOLAR", "36": "TROQUEL",
        "37": "SEÑALIZADOR DE CALLE", "43": "LED - TORRE UNIPOLAR",
        "44": "CAMION LED", "49": "TOTEM", "50": "LED - TORRE TRIPOLAR",
        "52": "LED - TORRE MINIPOLAR", "53": "PANEL / BANDEROLA",
        "54": "PANEL LED", "55": "VALLA LED", "56": "BASTIDOR"
    };

    tbody.querySelectorAll("tr").forEach(tr => {
        const check = tr.querySelector(".fila-check");
        if (check && check.checked) {
            const idUbicacion = tr.querySelector('input[name="codigo_ubicacion[]"]')?.value;
            if (idUbicacion) seleccionados.add(idUbicacion);
        }
    });

    data.forEach((item) => {
        // Evitar duplicados
        if (tbody.querySelector(`input[name="codigo_ubicacion[]"][value="${item.CodigoUbicacion}"]`)) {
            return; 
        }
        const codigoLimpio = (item.CodigoTipoElemento || "").trim();
        const descripcionVisual = mapaTipos[codigoLimpio] || codigoLimpio;
        const fila = `
        <tr data-id="${item.CodigoUbicacion}">
            <td>
                <input type="checkbox" class="fila-check">
                <input type="hidden" name="id_detalle[]" value="">
            </td>
            <td></td> 
            <td>${item.CodigoInterno || ""}
                <input type="hidden" name="codigo_ubicacion[]" value="${item.CodigoUbicacion}">
                <input type="hidden" name="codigo_provincia[]" value="${item.CodigoProvincia}">
                <input type="hidden" name="codigo_distrito[]" value="${item.CodigoDistrito}">
            </td>
            <td>${item.DireccionComercial || ""}</td>
            <td>${descripcionVisual}</td>
            <td>${item.Medidas || ""}</td>

            <td>
                <select name="estado_elemento[]" class="form-select form-select-sm">
                    <option value="">Seleccione</option>
                    <option value="01">Encendido</option>
                    <option value="02">Apagado</option>
                </select>
            </td>

            <td>
                <select name="punto_luz[]" class="form-select form-select-sm">
                    <option value="">Seleccione</option>
                    <option value="1">SI</option>
                    <option value="0">NO</option>
                </select>
            </td>

            <td>
                <input type="number" name="num_reflectores[]" class="form-control form-control-sm" value="0">
            </td>

            <td>
                <select name="estado_reflectores[]" class="form-select form-select-sm">
                    <option value="">Seleccione</option>
                    <option value="01">Encendidos</option>
                    <option value="02">Apagados</option>
                </select>
            </td>

            <td>
                <select name="publicidad_lona[]" class="form-select form-select-sm">
                    <option value="">Seleccione</option>
                    <option value="SI">SI</option>
                    <option value="NO">NO</option>
                </select>
            </td>

            <td>
                <select name="control_publicidad[]" class="form-select form-select-sm">
                    <option value="">—</option>
                    <option value="01">OK</option>
                    <option value="02">Renovar</option>
                    <option value="03">Retiro</option>
                    <option value="04">Cambio</option>
                </select>
            </td>

            <td>
                <select name="estado_lona[]" class="form-select form-select-sm">
                    <option value="">Seleccione</option>
                    <option value="01">En exhibición</option>
                    <option value="02">Vencido</option>
                </select>
            </td>
            <td>
                <select name="estado_logo[]" class="form-select form-select-sm">
                    <option value="">Seleccione</option>
                    <option value="01">TIENE</option>
                    <option value="02">NO TIENE</option>
                </select>
            </td>
            <td>
                <input type="text" name="observaciones[]" class="form-control form-control-sm">
            </td>
            <td>
                <button type="button" class="btn btn-outline-secondary btn-sm btn-foto"
                        onclick="this.nextElementSibling.click()">
                    <i class="bi bi-camera"></i> Fotos
                    <span class="badge bg-secondary foto-count ms-1" style="display:none">0</span>
                </button>
                <input type="file" name="fotos_${item.CodigoUbicacion}[]"
                    accept="image/*" multiple capture="environment"
                    style="display:none"
                    class="input-foto"
                    onchange="actualizarPreviewFotos(this)">
                <div class="foto-previews d-flex flex-wrap gap-1 mt-1"></div>
            </td>
        </tr>
        `;
        tbody.insertAdjacentHTML("beforeend", fila);
    });
    renumerarFilas();
}

    // =========================
    // LIMPIAR (BORRA NO MARCADOS)
    // =========================
document.getElementById("btn-limpiar").addEventListener("click", function () {

    if (!confirm("Se eliminarán las filas no marcadas. ¿Continuar?")) return;

    const filasMarcadas = Array.from(
        tbody.querySelectorAll("tr")
    ).filter(fila => fila.querySelector(".fila-check")?.checked);

    tbody.innerHTML = "";

    filasMarcadas.forEach(fila => tbody.appendChild(fila));

    renumerarFilas();
});


if (modoEdicion) {
    document.querySelectorAll("#tabla-body .fila-check").forEach(check => {
        check.checked = true;
    });
}
document.addEventListener("change", function(e) {
    if (e.target.classList.contains("fila-check")) {
        const fila = e.target.closest("tr");

        if (e.target.checked) {
            fila.classList.add("fila-activa");
        } else {
            fila.classList.remove("fila-activa");
        }
    }
});
function obtenerSeleccionados() {
    const seleccionados = new Set();
    document.querySelectorAll("#tabla-body tr").forEach(tr => {
        const check = tr.querySelector(".fila-check");
        if (check && check.checked) {
            seleccionados.add(tr.dataset.id);
        }
    });
    return seleccionados;
}

window.actualizarPreviewFotos = function(input) {
    const container = input.nextElementSibling;
    const badge = input.closest("td").querySelector(".btn-foto .foto-count");

    // Acumular archivos con DataTransfer
    const dt = new DataTransfer();
    if (input._archivosAcumulados) {
        input._archivosAcumulados.forEach(f => dt.items.add(f));
    }
    Array.from(input.files).forEach(f => dt.items.add(f));
    input.files = dt.files;
    input._archivosAcumulados = Array.from(dt.files);

    // Re-renderizar todas las miniaturas
    container.innerHTML = "";
    input._archivosAcumulados.forEach(file => {
        const reader = new FileReader();
        reader.onload = e => {
            const thumb = document.createElement("div");
            thumb.className = "foto-thumb position-relative";
            thumb.style.cssText = "width:44px;height:44px;flex-shrink:0;";
            thumb.innerHTML = `
                <img src="${e.target.result}"
                     data-preview="${e.target.result}"
                     style="width:100%;height:100%;object-fit:cover;
                            border-radius:4px;border:1px solid #ccc;cursor:zoom-in;">
                <span data-nombre="${file.name}"
                      onclick="event.stopPropagation();eliminarFotoNueva(this)"
                      style="position:absolute;top:1px;right:1px;
                             background:rgba(200,0,0,0.75);color:#fff;
                             border-radius:50%;width:16px;height:16px;font-size:10px;
                             display:flex;align-items:center;justify-content:center;
                             cursor:pointer;line-height:1;font-weight:bold;">✕</span>`;
            container.appendChild(thumb);
        };
        reader.readAsDataURL(file);
    });

    const total = input._archivosAcumulados.length;
    badge.textContent = total;
    badge.style.display = total > 0 ? "inline" : "none";
};

window.eliminarFotoNueva = function(btnEl) {
    const td = btnEl.closest("td");
    const input = td.querySelector(".input-foto");
    const nombre = btnEl.dataset.nombre;
    if (!input || !input._archivosAcumulados) return;

    input._archivosAcumulados = input._archivosAcumulados.filter(f => f.name !== nombre);

    const dt = new DataTransfer();
    input._archivosAcumulados.forEach(f => dt.items.add(f));
    input.files = dt.files;

    btnEl.closest(".foto-thumb").remove();

    const badge = td.querySelector(".btn-foto .foto-count");
    const total = input._archivosAcumulados.length;
    badge.textContent = total;
    badge.style.display = total > 0 ? "inline" : "none";
};

window.actualizarContadorFoto = function(celda) {
    if (!celda) return;
    const thumbs = celda.querySelectorAll(".foto-thumb").length;
    const badge = celda.querySelector(".foto-count");
    if (!badge) return;
    badge.textContent = thumbs;
    badge.style.display = thumbs > 0 ? "inline" : "none";
};

document.addEventListener("click", function(e) {
    const img = e.target.closest("img[data-preview]");
    if (!img) return;
    const modal = document.getElementById("modal-foto");
    if (!modal) return;
    document.getElementById("modal-foto-img").src = img.dataset.preview;
    modal.style.display = "flex";
});

document.addEventListener("keydown", function(e) {
    if (e.key === "Escape") {
        const modal = document.getElementById("modal-foto");
        if (modal) modal.style.display = "none";
    }
});
window.borrarFotoExistente = function(fotoId, btnEl) {
    if (!confirm("¿Borrar esta foto?")) return;

    fetch(`/inspeccion/foto/borrar/${fotoId}/`, {
        method: "POST",
        headers: {
            "X-CSRFToken": document.querySelector("[name=csrfmiddlewaretoken]").value
        }
    })
    .then(res => res.json())
    .then(data => {
        if (data.ok) {
            const thumb = document.getElementById(`foto-thumb-${fotoId}`);
            if (thumb) thumb.remove();
        } else {
            alert("Error al borrar la foto");
        }
    })
    .catch(() => alert("Error de conexión"));
};
});
