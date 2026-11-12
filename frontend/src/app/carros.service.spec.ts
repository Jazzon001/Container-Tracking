import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_URL } from './api.config';
import { Carro } from './carro.model';
import { CarroNoExiste, CarrosService } from './carros.service';

const CARRO: Carro = {
  id: 7,
  numero: 'C-007',
  estado: 'disponible',
  contenedor_elemento: null,
  estado_desde: '2026-11-12T12:00:00Z',
};

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

  afterEach(() => http.verify());

  describe('listar', () => {
    it('lista todos los carros', () => {
      let recibidos: Carro[] = [];
      servicio.listar().subscribe((carros) => (recibidos = carros));

      const peticion = http.expectOne('http://api.test/carros');
      expect(peticion.request.method).toBe('GET');
      peticion.flush([CARRO]);

      expect(recibidos).toEqual([CARRO]);
    });

    it('no envía filtros: la pantalla filtra en el cliente', () => {
      servicio.listar().subscribe();

      const peticion = http.expectOne('http://api.test/carros');
      expect(peticion.request.params.keys().length).toBe(0);
      peticion.flush([]);
    });
  });

  describe('buscarPorNumero', () => {
    it('devuelve el carro que tiene ese número', () => {
      let resultado: Carro | undefined;
      servicio.buscarPorNumero('C-007').subscribe((carro) => (resultado = carro));

      const peticion = http.expectOne('http://api.test/carros?numero=C-007');
      expect(peticion.request.method).toBe('GET');
      peticion.flush([CARRO]);

      expect(resultado).toEqual(CARRO);
    });

    it('falla con CarroNoExiste si no hay ningún carro con ese número', () => {
      let error: unknown;
      servicio.buscarPorNumero('C-999').subscribe({ error: (e) => (error = e) });
      http.expectOne('http://api.test/carros?numero=C-999').flush([]);

      expect(error).toBeInstanceOf(CarroNoExiste);
    });
  });

  describe('cargarPorNumero', () => {
    it('busca el carro por su número y luego lo carga con el contenedor', () => {
      let resultado: Carro | undefined;
      servicio.cargarPorNumero('C-007', '100123').subscribe((carro) => (resultado = carro));

      http.expectOne('http://api.test/carros?numero=C-007').flush([CARRO]);

      const carga = http.expectOne('http://api.test/carros/7/carga');
      expect(carga.request.method).toBe('POST');
      expect(carga.request.body).toEqual({ contenedor_elemento: '100123' });
      carga.flush({ ...CARRO, estado: 'en_transito', contenedor_elemento: '100123' });

      expect(resultado?.estado).toBe('en_transito');
    });

    it('falla con CarroNoExiste y no intenta cargar si el número no existe', () => {
      let error: unknown;
      servicio.cargarPorNumero('C-999', '100123').subscribe({ error: (e) => (error = e) });

      http.expectOne('http://api.test/carros?numero=C-999').flush([]);

      expect(error).toBeInstanceOf(CarroNoExiste);
      expect((error as Error).message).toBe('No existe un carro con el número C-999');
      http.expectNone('http://api.test/carros/7/carga');
    });

    it('deja pasar el error de la API (por ejemplo, un 409)', () => {
      let estado = 0;
      servicio.cargarPorNumero('C-007', '100123').subscribe({ error: (e) => (estado = e.status) });

      http.expectOne('http://api.test/carros?numero=C-007').flush([CARRO]);
      http.expectOne('http://api.test/carros/7/carga').flush({}, { status: 409, statusText: 'Conflict' });

      expect(estado).toBe(409);
    });
  });

  describe('entregarPorNumero', () => {
    it('busca el carro por su número y luego lo entrega', () => {
      let resultado: Carro | undefined;
      servicio.entregarPorNumero('C-007').subscribe((carro) => (resultado = carro));

      http.expectOne('http://api.test/carros?numero=C-007').flush([{ ...CARRO, estado: 'en_transito' }]);

      const entrega = http.expectOne('http://api.test/carros/7/entrega');
      expect(entrega.request.method).toBe('POST');
      entrega.flush(CARRO);

      expect(resultado?.estado).toBe('disponible');
    });

    it('falla con CarroNoExiste si el número no existe', () => {
      let error: unknown;
      servicio.entregarPorNumero('C-999').subscribe({ error: (e) => (error = e) });

      http.expectOne('http://api.test/carros?numero=C-999').flush([]);

      expect(error).toBeInstanceOf(CarroNoExiste);
    });
  });
});
