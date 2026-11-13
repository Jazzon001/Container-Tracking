import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { API_URL } from './api.config';
import { Carro } from './carro.model';
import { CarroNoExiste, CarrosService, ContenedorNoEncontrado } from './carros.service';

const CARRO: Carro = {
  id: 7,
  numero: 'C-007',
  tipo: 'poy',
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

  describe('entregarPorContenedor', () => {
    const EN_TRANSITO: Carro = { ...CARRO, estado: 'en_transito', contenedor_elemento: '100123' };

    it('busca el carro por el contenedor elemento que lleva y luego lo entrega', () => {
      let resultado: Carro | undefined;
      servicio.entregarPorContenedor('100123').subscribe((carro) => (resultado = carro));

      http.expectOne('http://api.test/carros?contenedor_elemento=100123').flush([EN_TRANSITO]);

      const entrega = http.expectOne('http://api.test/carros/7/entrega');
      expect(entrega.request.method).toBe('POST');
      entrega.flush(CARRO);

      expect(resultado?.estado).toBe('disponible');
    });

    it('no busca por el número del carro', () => {
      servicio.entregarPorContenedor('100123').subscribe();

      const busqueda = http.expectOne('http://api.test/carros?contenedor_elemento=100123');
      expect(busqueda.request.params.get('contenedor_elemento')).toBe('100123');
      expect(busqueda.request.params.has('numero')).toBe(false);
      busqueda.flush([EN_TRANSITO]);
      http.expectOne('http://api.test/carros/7/entrega').flush(CARRO);
    });

    it('falla con ContenedorNoEncontrado y no entrega nada si ningún carro lo lleva', () => {
      let error: unknown;
      servicio.entregarPorContenedor('999999').subscribe({ error: (e) => (error = e) });

      http.expectOne('http://api.test/carros?contenedor_elemento=999999').flush([]);

      expect(error).toBeInstanceOf(ContenedorNoEncontrado);
      expect((error as Error).message).toBe(
        'No hay ningún carro en tránsito con el contenedor elemento 999999',
      );
      http.expectNone('http://api.test/carros/7/entrega');
    });

    it('deja pasar el error de la API', () => {
      let estado = 0;
      servicio.entregarPorContenedor('100123').subscribe({ error: (e) => (estado = e.status) });

      http.expectOne('http://api.test/carros?contenedor_elemento=100123').flush([EN_TRANSITO]);
      http.expectOne('http://api.test/carros/7/entrega').flush({}, { status: 409, statusText: 'Conflict' });

      expect(estado).toBe(409);
    });
  });
});
