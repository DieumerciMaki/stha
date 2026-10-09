import {useEffect,useRef,useState} from 'react';
import L from 'leaflet';
import {Camera, ChevronLeft, ChevronRight, MapPin, Search, X} from 'lucide-react';
import {dateLabel} from './api';
import type {Analysis, Observation} from './types';

export function Status({analysis}:{analysis:Analysis|null}) {
  const status=analysis?.status||'none';
  const labels={none:'À analyser',queued:'En attente',running:'En cours',completed:'Terminée',failed:'Échec'};
  return <span className={'status-badge '+status}><span/>{labels[status]}</span>;
}
export function ReviewStatus({analysis}:{analysis:Analysis|null}) {
  const decision=analysis?.latest_review?.decision;
  return <span className={'review-label '+(decision||'pending')}>{decision==='accepted'?'Accepté':decision==='rejected'?'Rejeté':'À vérifier'}</span>;
}
export function Empty({title,children,icon='image'}:{title:string;children?:React.ReactNode;icon?:'image'|'map'}) {
  return <div className="empty-state">{icon==='map'?<MapPin size={30}/>:<Camera size={30}/>}<h3>{title}</h3>{children}</div>;
}
export function Modal({title,children,onClose,wide=false}:{title:string;children:React.ReactNode;onClose:()=>void;wide?:boolean}){
  const ref=useRef<HTMLDialogElement>(null);
  useEffect(()=>{const dialog=ref.current!;dialog.showModal();return ()=>dialog.close();},[]);
  return <dialog ref={ref} className={wide?'modal wide':'modal'} onCancel={onClose} onClick={e=>{if(e.target===e.currentTarget){const r=e.currentTarget.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)onClose();}}}><div className="modal-header"><h2>{title}</h2><button className="icon-button" aria-label="Fermer" onClick={onClose}><X size={20}/></button></div>{children}</dialog>;
}
export function SearchField({value,onChange,placeholder='Rechercher une observation'}:{value:string;onChange:(value:string)=>void;placeholder?:string}){
  return <label className="search-field"><Search size={16}/><span className="sr-only">{placeholder}</span><input type="search" placeholder={placeholder} value={value} onChange={e=>onChange(e.target.value)}/></label>;
}
export function ObservationTable({rows,onOpen,compact=false}:{rows:Observation[];onOpen:(row:Observation)=>void;compact?:boolean}){
  const [page,setPage]=useState(0);
  const pageSize=10;
  useEffect(()=>setPage(0),[rows]);
  const pageRows=compact?rows.slice(0,5):rows.slice(page*pageSize,(page+1)*pageSize);
  return <><div className="table-scroll"><table className="observation-table"><thead><tr><th>Photographie</th><th>Quartier</th><th>Date d’ajout</th><th>Analyse</th><th><span className="sr-only">Action</span></th></tr></thead><tbody>{pageRows.map(row=><tr key={row.id}><td><div className="photo-cell"><img src={row.image_url} alt="" loading="lazy"/><div><button className="title-link" onClick={()=>onOpen(row)}>{row.title}</button>{!compact&&<small>{row.id.slice(0,8).toUpperCase()}</small>}</div></div></td><td>{row.neighborhood||'—'}</td><td className="nowrap">{dateLabel(row.created_at)}</td><td><Status analysis={row.latest_analysis}/></td><td><button className="text-button" aria-label={'Ouvrir '+row.title} onClick={()=>onOpen(row)}>Ouvrir</button></td></tr>)}</tbody></table></div>{!rows.length&&<Empty title="Aucune observation"><p>Ajoutez une photographie ou modifiez les filtres.</p></Empty>}{!compact&&rows.length>0&&<div className="pagination"><span>{rows.length} observation{rows.length>1?'s':''}</span><div><button className="icon-button" aria-label="Page précédente" disabled={page===0} onClick={()=>setPage(page-1)}><ChevronLeft size={17}/></button><span>{page+1} / {Math.ceil(rows.length/pageSize)}</span><button className="icon-button" aria-label="Page suivante" disabled={(page+1)*pageSize>=rows.length} onClick={()=>setPage(page+1)}><ChevronRight size={17}/></button></div></div>}</>;
}
export function ObservationMap({rows,onOpen,large=false}:{rows:Observation[];onOpen:(row:Observation)=>void;large?:boolean}){
  const container=useRef<HTMLDivElement>(null);
  const map=useRef<L.Map|null>(null);
  const group=useRef<L.LayerGroup|null>(null);
  const open=useRef(onOpen);open.current=onOpen;
  const [tileError,setTileError]=useState(false);
  useEffect(()=>{
    const instance=L.map(container.current!,{scrollWheelZoom:large,attributionControl:true}).setView([-1.678,29.228],12);
    const tiles=L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{attribution:'© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',maxZoom:19,referrerPolicy:'strict-origin-when-cross-origin'}).addTo(instance);
    tiles.on('tileerror',()=>setTileError(true));
    group.current=L.layerGroup().addTo(instance);map.current=instance;
    const observer=new ResizeObserver(()=>instance.invalidateSize());observer.observe(container.current!);
    return ()=>{observer.disconnect();instance.remove();map.current=null;};
  },[large]);
  useEffect(()=>{
    if(!map.current||!group.current)return;
    group.current.clearLayers();
    const located=rows.filter(x=>x.latitude!==null&&x.longitude!==null);
    for(const row of located){
      const marker=L.circleMarker([row.latitude!,row.longitude!],{radius:8,color:'#fff',weight:2,fillColor:row.latest_analysis?.status==='completed'?'#25475a':'#97733c',fillOpacity:1});
      const popup=document.createElement('div');
      const title=document.createElement('strong');title.textContent=row.title;popup.append(title);
      const info=document.createElement('p');info.textContent=row.neighborhood||row.location;popup.append(info);
      const button=document.createElement('button');button.textContent='Ouvrir l’observation';button.className='map-open';button.onclick=()=>open.current(row);popup.append(button);
      marker.bindPopup(popup).addTo(group.current);
    }
    if(located.length){map.current.fitBounds(L.latLngBounds(located.map(x=>[x.latitude!,x.longitude!] as [number,number])),{padding:[30,30],maxZoom:15});}
  },[rows]);
  const count=rows.filter(x=>x.latitude!==null).length;
  return <div className={'map-wrapper '+(large?'large':'')}><div ref={container} className="map-canvas" aria-label="Carte des observations géolocalisées"/>{!count&&<div className="map-empty">Aucune observation géolocalisée</div>}{tileError&&<p className="map-warning">Le fond de carte nécessite une connexion Internet.</p>}</div>;
}
