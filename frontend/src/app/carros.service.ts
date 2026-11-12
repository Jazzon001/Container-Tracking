import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, map, of, switchMap, throwError } from 'rxjs';
import { API_URL } from './api.config';
import { Carro } from './carro.model';

/** El número escaneado o escrito no corresponde a ningún carro registrado. */
export class CarroNoExiste extends Error {
  constructor(numero: string) {
    super(`No existe un carro con el número ${numero}`);
  }
}

/** Ningún carro en tránsito lleva ese contenedor elemento. */
export class ContenedorNoEncontrado extends Error {
  constructor(contenedorElemento: string) {
    super(`No hay ningún carro en tránsito con el contenedor elemento ${contenedorElemento}`);
  }
}

@Injectable({ providedIn: 'root' })
export class CarrosService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  /** Trae todos los carros. La pantalla los filtra y cuenta por su cuenta. */
  listar(): Observable<Carro[]> {
    return this.http.get<Carro[]>(`${this.apiUrl}/carros`);
  }

  /**
   * La API opera por id, pero las personas escanean el número del carro.
   * Falla con CarroNoExiste si ese número no está registrado.
   */
  buscarPorNumero(numero: string): Observable<Carro> {
    return this.buscarUno({ numero }, new CarroNoExiste(numero));
  }

  /** POY carga un carro: lo asocia con el código de su contenedor elemento. */
  cargarPorNumero(numero: string, contenedorElemento: string): Observable<Carro> {
    return this.buscarPorNumero(numero).pipe(
      switchMap((carro) =>
        this.http.post<Carro>(`${this.apiUrl}/carros/${carro.id}/carga`, {
          contenedor_elemento: contenedorElemento,
        }),
      ),
    );
  }

  /**
   * Almacén recibe un carro vacío. Se identifica por el contenedor elemento que llevaba,
   * que es lo que lo hace único mientras está en tránsito. Queda disponible para POY.
   */
  entregarPorContenedor(contenedorElemento: string): Observable<Carro> {
    return this.buscarUno(
      { contenedor_elemento: contenedorElemento },
      new ContenedorNoEncontrado(contenedorElemento),
    ).pipe(
      switchMap((carro) => this.http.post<Carro>(`${this.apiUrl}/carros/${carro.id}/entrega`, {})),
    );
  }

  /** Busca un carro por un campo exacto; si no hay ninguno, falla con el error indicado. */
  private buscarUno(filtro: Record<string, string>, noEncontrado: Error): Observable<Carro> {
    const params = new HttpParams({ fromObject: filtro });
    return this.http.get<Carro[]>(`${this.apiUrl}/carros`, { params }).pipe(
      map((carros) => carros[0]),
      switchMap((carro) => (carro ? of(carro) : throwError(() => noEncontrado))),
    );
  }
}
