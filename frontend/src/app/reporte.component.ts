import { Component, computed, inject, signal } from '@angular/core';
import { mensajeDeApi } from './api-error';
import { DescargaService } from './descarga.service';
import { FilaCarroReporte, ReporteCarros } from './reporte.model';
import { ReporteService } from './reporte.service';

@Component({
  selector: 'app-reporte',
  template: `
    <h1>Reporte de carros</h1>
    <p class="ayuda">
      Sube el Excel de movimientos de NOW (plantillas 016 y 202). El reporte mide cuánto tiempo pasó cada carro en
      RCV01, en WIP y en DTY, y lo cruza con lo que se registró en este sistema. El archivo no se guarda.
    </p>

    <form (submit)="generar($event)">
      <label>
        Excel de NOW
        <input
          type="file"
          name="archivo"
          accept=".xlsx"
          (change)="elegirArchivo($event)"
        />
      </label>
      <div class="acciones">
        <button type="submit" [disabled]="!archivo() || generando()">
          {{ generando() ? 'Generando…' : 'Generar reporte' }}
        </button>
        @if (reporte()) {
          <button type="button" class="secundario" [disabled]="descargando()" (click)="descargar()">
            {{ descargando() ? 'Preparando…' : 'Descargar Excel' }}
          </button>
        }
      </div>
    </form>

    @if (error()) { <p role="alert">{{ error() }}</p> }

    @if (reporte(); as datos) {
      <p class="detalle">Medido al último movimiento del archivo: {{ datos.corte }} (hora de NOW)</p>

      <h2>Resumen</h2>
      <dl class="resumen">
        @for (fila of datos.resumen; track fila.indicador) {
          <div>
            <dt>{{ fila.indicador }}</dt>
            <dd>{{ fila.valor }}</dd>
          </div>
        }
      </dl>

      @for (tabla of datos.tablas; track tabla.titulo) {
        @if (tabla.filas.length) {
          <h2>{{ tabla.titulo }}</h2>
          <div class="tabla">
            <table>
              <thead>
                <tr><th>{{ tabla.columna }}</th><th>Viajes</th><th>Horas promedio</th><th>Horas máximo</th></tr>
              </thead>
              <tbody>
                @for (fila of tabla.filas; track fila.clave) {
                  <tr><td>{{ fila.clave }}</td><td>{{ fila.viajes }}</td><td>{{ fila.promedio }}</td><td>{{ fila.maximo }}</td></tr>
                }
              </tbody>
            </table>
          </div>
        }
      }

      <h2>Por carro</h2>
      <p class="ayuda">Cada carro se parte en un lado A y un lado B. Aquí ves el último contenedor elemento de cada lado; el Excel trae una fila por contenedor elemento, con la etapa en que está y las horas en cada una. "En este sistema" es el último contenedor del carro que se cargó en la aplicación.</p>
      <label>
        Buscar carro
        <input type="search" name="buscar" autocomplete="off" autocapitalize="characters" #caja [value]="busqueda()" (input)="busqueda.set(caja.value)" />
      </label>
      <p class="detalle">{{ visibles().length }} de {{ datos.carros.length }} carros (lados)</p>
      <div class="tabla">
        <table>
          <thead>
            <tr>
              <th>Carro</th><th>Calidad</th><th>Situación (NOW)</th><th>Horas ahí</th>
              <th>En este sistema</th><th>Horas en DTY</th>
            </tr>
          </thead>
          <tbody>
            @for (carro of visibles(); track carro.carro) {
              <tr>
                <td>{{ carro.carro }}</td>
                <td>{{ carro.calidad }}</td>
                <td>{{ carro.situacion }}</td>
                <td>{{ horas(carro.horas_en_situacion) }}</td>
                <td>{{ carro.situacion_sistema }}</td>
                <td>{{ horasEnDty(carro) }}</td>
              </tr>
            } @empty {
              <tr><td colspan="6" class="vacio">No hay carros para mostrar</td></tr>
            }
          </tbody>
        </table>
      </div>
    }
  `,
  styles: `
    .ayuda { margin: 0 0 1rem; color: var(--color-suave); }
    form { max-width: none; margin: 0 0 1rem; }
    .acciones { display: flex; flex-wrap: wrap; gap: 0.75rem; }
    .detalle { margin: 0 0 0.5rem; color: var(--color-suave); }
    h2 { margin: 1.5rem 0 0.5rem; font-size: 1.125rem; }
    .resumen { margin: 0; }
    .resumen div { display: flex; justify-content: space-between; gap: 1rem; padding: 0.375rem 0; border-bottom: 1px solid var(--color-borde); }
    .resumen dt { color: var(--color-suave); }
    .resumen dd { margin: 0; font-weight: 600; text-align: right; }
    .tabla { overflow-x: auto; }
    table { width: 100%; border-collapse: collapse; font-size: 0.875rem; }
    th, td { padding: 0.375rem 0.5rem; text-align: left; border-bottom: 1px solid var(--color-borde); }
    .vacio { padding: 1.5rem 0; text-align: center; color: var(--color-suave); }
  `,
})
export class ReporteComponent {
  private readonly servicio = inject(ReporteService);
  private readonly descargas = inject(DescargaService);

  readonly archivo = signal<File | null>(null);
  readonly reporte = signal<ReporteCarros | null>(null);
  readonly generando = signal(false);
  readonly descargando = signal(false);
  readonly error = signal('');
  readonly busqueda = signal('');

  readonly visibles = computed(() => {
    const texto = this.busqueda().trim().toUpperCase();
    const carros = this.reporte()?.carros ?? [];
    return texto ? carros.filter((carro) => carro.carro.toUpperCase().includes(texto)) : carros;
  });

  elegirArchivo(evento: Event): void {
    this.archivo.set((evento.target as HTMLInputElement).files?.[0] ?? null);
    this.reporte.set(null);
    this.error.set('');
  }

  generar(evento: Event): void {
    evento.preventDefault();
    const archivo = this.archivo();
    if (!archivo) return;
    this.generando.set(true);
    this.error.set('');
    this.servicio.generar(archivo).subscribe({
      next: (reporte) => {
        this.reporte.set(reporte);
        this.busqueda.set('');
        this.generando.set(false);
      },
      error: (fallo) => {
        this.reporte.set(null);
        this.error.set(mensajeDeApi(fallo, 'No se pudo generar el reporte'));
        this.generando.set(false);
      },
    });
  }

  descargar(): void {
    const archivo = this.archivo();
    if (!archivo) return;
    this.descargando.set(true);
    this.servicio.descargarExcel(archivo).subscribe({
      next: (contenido) => {
        this.descargas.guardar(contenido, 'reporte_carros.xlsx');
        this.descargando.set(false);
      },
      error: () => {
        // El error llega como un archivo, no como texto: se avisa con un mensaje general.
        this.error.set('No se pudo preparar el Excel');
        this.descargando.set(false);
      },
    });
  }

  horas(valor: number | null): string {
    return valor === null ? '—' : `${valor} h`;
  }

  horasEnDty(carro: FilaCarroReporte): string {
    if (carro.horas_en_dty === null) return '—';
    return carro.dty_abierto ? `${carro.horas_en_dty} h (sin liberar)` : `${carro.horas_en_dty} h`;
  }
}
