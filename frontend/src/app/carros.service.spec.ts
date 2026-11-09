import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_URL } from './api.config';
import { Carro } from './carro.model';
import { CarrosService } from './carros.service';

describe('CarrosService', () => {
  let servicio: CarrosService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: 'http://api.test' },
      ],
    });
    servicio = TestBed.inject(CarrosService);
    http = TestBed.inject(HttpTestingController);
  });

  it('lista todos los carros sin filtro', () => {
    let recibidos: Carro[] = [];
    servicio.listar().subscribe((carros) => (recibidos = carros));

    const peticion = http.expectOne('http://api.test/carros');
    expect(peticion.request.method).toBe('GET');
    peticion.flush([{ id: 1, numero: 'C-001', estado: 'disponible', contenedor_elemento: null }]);

    expect(recibidos.length).toBe(1);
    expect(recibidos[0].numero).toBe('C-001');
  });

  it('envía el estado como parámetro para filtrar', () => {
    servicio.listar('en_transito').subscribe();

    const peticion = http.expectOne('http://api.test/carros?estado=en_transito');
    expect(peticion.request.params.get('estado')).toBe('en_transito');
    peticion.flush([]);
  });
});
