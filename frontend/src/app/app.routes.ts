import { Routes } from '@angular/router';
import { authGuard } from './auth.guard';
import { CarrosComponent } from './carros.component';
import { LoginComponent } from './login.component';

export const routes: Routes = [
  { path: 'login', component: LoginComponent },
  { path: 'carros', component: CarrosComponent, canActivate: [authGuard] },
  { path: '', redirectTo: 'carros', pathMatch: 'full' },
];
