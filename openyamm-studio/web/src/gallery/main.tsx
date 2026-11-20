import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import '../styles/global.css';
import '../styles/views.css';
import { probe } from '../app/controller.ts';
import { Gallery } from './Gallery.tsx';

probe();
document.body.classList.add('oy-gallery');
window.addEventListener('error', (event) => probe().errors.push(String(event.message)));
const params = new URLSearchParams(location.search);
if (params.get('theme'))
{
    document.documentElement.dataset.theme = params.get('theme')!;
}
createRoot(document.getElementById('root')!).render(<StrictMode><Gallery /></StrictMode>);
