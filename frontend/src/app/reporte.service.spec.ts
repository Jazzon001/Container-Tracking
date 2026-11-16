import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_URL } from './api.config';
import { ReporteCarros } from './reporte.model';
import { ReporteService } from './reporte.service';

const REPORTE: ReporteCarros = { corte: '16/11/2026 11:07', resumen: [], tablas: [], carros: [] };

describe('ReporteService', () => {
  let servicio: ReporteService;
  let http: HttpTestingController;
  const archivo = new File(['contenido'], 'movimientos.xlsx');

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: 'http://api.test' },
      ],
    });
    servicio = TestBed.inject(ReporteService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('envía el Excel tal cual en el cuerpo de la petición, no como un formulario', () => {
    let recibido: ReporteCarros | undefined;
    servicio.generar(archivo).subscribe((reporte) => (recibido = reporte));

    const peticion = http.expectOne('http://api.test/reportes/carros');
    expect(peticion.request.method).toBe('POST');
    expect(peticion.request.body).toBe(archivo);
    expect(peticion.request.headers.get('Content-Type')).toBe('application/octet-stream');
    peticion.flush(REPORTE);

    expect(recibido).toEqual(REPORTE);
  });

  it('pide el Excel del reporte como un archivo', () => {
    let recibido: Blob | undefined;
    servicio.descargarExcel(archivo).subscribe((contenido) => (recibido = contenido));

    const peticion = http.expectOne('http://api.test/reportes/carros/excel');
    expect(peticion.request.method).toBe('POST');
    expect(peticion.request.body).toBe(archivo);
    expect(peticion.request.responseType).toBe('blob');
    peticion.flush(new Blob(['xlsx']));

    expect(recibido).toBeInstanceOf(Blob);
  });
});
