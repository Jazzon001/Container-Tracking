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

@Injectable({ providedIn: 'root' })
export class CarrosService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  /** Trae todos los carros. La pantalla los filtra y cuenta por su cuenta. */
  listar(): Observable<Carro[]> {
    return this.http.get<Carro[]>(`${this.apiUrl}/carros`);
  }

  /** POY carga un carro: lo asocia con el código de su contenedor elemento. */
  cargarPorNumero(numero: string, contenedorElemento: string): Observable<Carro> {
    return this.buscar(numero).pipe(
      switchMap((carro) =>
        this.http.post<Carro>(`${this.apiUrl}/carros/${carro.id}/carga`, {
          contenedor_elemento: contenedorElemento,
        }),
      ),
    );
  }

  /** Almacén recibe un carro vacío: queda disponible para POY. */
  entregarPorNumero(numero: string): Observable<Carro> {
    return this.buscar(numero).pipe(
      switchMap((carro) => this.http.post<Carro>(`${this.apiUrl}/carros/${carro.id}/entrega`, {})),
    );
  }

  /** La API opera por id, pero las personas escanean el número del carro. */
  private buscar(numero: string): Observable<Carro> {
    const params = new HttpParams().set('numero', numero);
    return this.http.get<Carro[]>(`${this.apiUrl}/carros`, { params }).pipe(
      map((carros) => carros[0]),
      switchMap((carro) => (carro ? of(carro) : throwError(() => new CarroNoExiste(numero)))),
    );
  }
}
