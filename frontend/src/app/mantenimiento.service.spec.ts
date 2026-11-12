import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_URL } from './api.config';
import { Carro } from './carro.model';
import { CarroNoExiste } from './carros.service';
import { Mantenimiento } from './mantenimiento.model';
import { MantenimientoService } from './mantenimiento.service';

const CARRO: Carro = {
  id: 7,
  numero: 'C-007',
  estado: 'disponible',
  contenedor_elemento: null,
  estado_desde: '2026-11-12T12:00:00Z',
};

const ABIERTO: Mantenimiento = {
  id: 1,
  carro_id: 7,
  fecha_entrada: '2026-11-12T13:00:00Z',
  fecha_salida: null,
};

describe('MantenimientoService', () => {
  let servicio: MantenimientoService;
  let http: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [
        provideHttpClient(),
        provideHttpClientTesting(),
        { provide: API_URL, useValue: 'http://api.test' },
      ],
    });
    servicio = TestBed.inject(MantenimientoService);
    http = TestBed.inject(HttpTestingController);
  });

  afterEach(() => http.verify());

  describe('iniciarPorNumero', () => {
    it('busca el carro por su número y luego registra la entrada a mantenimiento', () => {
      let resultado: Mantenimiento | undefined;
      servicio.iniciarPorNumero('C-007').subscribe((registro) => (resultado = registro));

      http.expectOne('http://api.test/carros?numero=C-007').flush([CARRO]);

      const entrada = http.expectOne('http://api.test/carros/7/mantenimiento');
      expect(entrada.request.method).toBe('POST');
      entrada.flush(ABIERTO);

      expect(resultado).toEqual(ABIERTO);
    });

    it('falla con CarroNoExiste y no registra nada si el número no existe', () => {
      let error: unknown;
      servicio.iniciarPorNumero('C-999').subscribe({ error: (e) => (error = e) });
      http.expectOne('http://api.test/carros?numero=C-999').flush([]);

      expect(error).toBeInstanceOf(CarroNoExiste);
      http.expectNone('http://api.test/carros/7/mantenimiento');
    });

    it('deja pasar el error de la API (por ejemplo, el carro no está disponible)', () => {
      let estado = 0;
      servicio.iniciarPorNumero('C-007').subscribe({ error: (e) => (estado = e.status) });

      http.expectOne('http://api.test/carros?numero=C-007').flush([CARRO]);
      http.expectOne('http://api.test/carros/7/mantenimiento').flush({}, { status: 409, statusText: 'Conflict' });

      expect(estado).toBe(409);
    });
  });

  describe('finalizar', () => {
    it('registra la salida de mantenimiento del carro indicado', () => {
      let resultado: Mantenimiento | undefined;
      servicio.finalizar(7).subscribe((registro) => (resultado = registro));

      const salida = http.expectOne('http://api.test/carros/7/mantenimiento/salida');
      expect(salida.request.method).toBe('POST');
      salida.flush({ ...ABIERTO, fecha_salida: '2026-11-12T15:00:00Z' });

      expect(resultado?.fecha_salida).toBe('2026-11-12T15:00:00Z');
    });
  });
});
