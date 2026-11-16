import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { API_URL } from './api.config';
import { ReporteCarros } from './reporte.model';

/** El Excel viaja tal cual en el cuerpo de la petición: la API no necesita un formulario multipart. */
const ENCABEZADOS = new HttpHeaders({ 'Content-Type': 'application/octet-stream' });

@Injectable({ providedIn: 'root' })
export class ReporteService {
  private readonly http = inject(HttpClient);
  private readonly apiUrl = inject(API_URL);

  /** El reporte de tiempos del Excel de NOW, cruzado con las cargas del sistema. La API no guarda el archivo. */
  generar(archivo: File): Observable<ReporteCarros> {
    return this.http.post<ReporteCarros>(`${this.apiUrl}/reportes/carros`, archivo, { headers: ENCABEZADOS });
  }

  /** El mismo reporte como un archivo Excel. */
  descargarExcel(archivo: File): Observable<Blob> {
    return this.http.post(`${this.apiUrl}/reportes/carros/excel`, archivo, {
      headers: ENCABEZADOS,
      responseType: 'blob',
    });
  }
}
