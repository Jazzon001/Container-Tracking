import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_URL } from './api.config';
import { HistorialService } from './historial.service';
import { RegistroCarga } from './registro-carga.model';

const REGISTRO: RegistroCarga = {
  id: 1,
  carro_id: 7,
  carro_numero: 'P001A',
  contenedor_elemento: '100123',
  cargada_en: '2026-11-12T08:00:00Z',
  recibida_en: null,
};

describe('HistorialService', () => {
  let servicio: HistorialService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: 'http://api.test' },
      ],
    });
    servicio = TestBed.inject(HistorialService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  it('pide los últimos 100 viajes cuando no hay filtros', () => {
    let recibidos: RegistroCarga[] = [];
    servicio.listar().subscribe((registros) => (recibidos = registros));

    const peticion = http.expectOne('http://api.test/cargas?limite=100');
    expect(peticion.request.method).toBe('GET');
    peticion.flush([REGISTRO]);

    expect(recibidos).toEqual([REGISTRO]);
  });

  it('filtra por el número del carro', () => {
    servicio.listar({ numero: 'P001A' }).subscribe();
    http.expectOne('http://api.test/cargas?limite=100&numero=P001A').flush([]);
  });

  it('filtra por el contenedor elemento', () => {
    servicio.listar({ contenedor: '100123' }).subscribe();
    http.expectOne('http://api.test/cargas?limite=100&contenedor_elemento=100123').flush([]);
  });

  it('combina los dos filtros', () => {
    servicio.listar({ numero: 'P001A', contenedor: '100123' }).subscribe();
    http.expectOne('http://api.test/cargas?limite=100&numero=P001A&contenedor_elemento=100123').flush([]);
  });

  it('ignora los filtros vacíos', () => {
    servicio.listar({ numero: '', contenedor: '' }).subscribe();
    http.expectOne('http://api.test/cargas?limite=100').flush([]);
  });

  it('permite cambiar el límite', () => {
    servicio.listar({}, 500).subscribe();
    http.expectOne('http://api.test/cargas?limite=500').flush([]);
  });
});
