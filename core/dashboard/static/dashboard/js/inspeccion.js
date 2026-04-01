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

 function cargarTabla(data) {

    const tbody = document.getElementById("tabla-body");

    // ✅ obtener seleccionados actuales
    const seleccionados = new Set();
    tbody.querySelectorAll("tr").forEach(tr => {
        const check = tr.querySelector(".fila-check");
        if (check && check.checked) {
            seleccionados.add(tr.dataset.id);
        }
    });

    data.forEach((item) => {

        // ❌ evitar duplicados
        if (tbody.querySelector(`tr[data-id="${item.CodigoUbicacion}"]`)) {
            return;
        }

        // ✅ mantener selección previa
        const checked = seleccionados.has(item.CodigoUbicacion) ? "checked" : "";

        const fila = `
        
        <tr data-id="${item.CodigoUbicacion}">
            <td><input type="checkbox" class="fila-check" ${checked}></td>
            <td></td>

            <td>${item.CodigoInterno || ""}</td>
                <input type="hidden" name="codigo_ubicacion[]" value="${item.CodigoUbicacion}">
                <input type="hidden" name="codigo_provincia[]" value="${item.CodigoProvincia}">
                <input type="hidden" name="codigo_distrito[]" value="${item.CodigoDistrito}">
            <td>${item.DireccionComercial || ""}</td>


            <td>${item.CodigoTipoElemento || ""}</td>
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

            <td><input type="number" name="num_reflectores[]" class="form-control form-control-sm"></td>

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
                    <option value="1">SI</option>
                    <option value="0">NO</option>
                </select>
            </td>

            <td>
                <select name="control_publicidad[]" class="form-select form-select-sm">
                    <option value="">—</option>
                    <option value="01">OK</option>
                    <option value="02">Renovar</option>
                    <option value="03">Retiro</option>
                    <option value="04">Cambio</option>
                    <option value="05">Mantenimiento</option>
                    <option value="06">Urgente</option>
                    <option value="07">Bloquear</option>
                    <option value="08">Liberar</option>
                </select>
            </td>

            <td>
                <select name="estado_lona[]" class="form-select form-select-sm">
                    <option value="">Seleccione</option>
                    <option value="01">En exhibición</option>
                    <option value="02">Vencido</option>
                    <option value="03">Reservado</option>
                    <option value="04">Observación</option>
                    <option value="05">Dañado</option>
                    <option value="06">Retiro</option>
                    <option value="07">Fuera contrato</option>
                    <option value="08">Suspendido</option>
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
        </tr>
        `;

        // ✅ IMPORTANTE: NO reemplazar, solo agregar
        tbody.insertAdjacentHTML("beforeend", fila);
    });

    ordenarMarcados();
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

    // =========================
    // ORDENAR MARCADOS ARRIBA
    // =========================
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

    // =========================
    // NUMERAR FILAS
    // =========================
    function renumerarFilas() {

        const filas = tbody.querySelectorAll("tr");

        filas.forEach((fila, index) => {
            fila.children[1].textContent = index + 1;
        });
    }

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
});
