import {useEffect, useRef, useState} from 'react';
import {ChevronUp, LogOut, PanelLeftClose, PanelLeftOpen, Recycle, Settings} from 'lucide-react';
import type {LucideIcon} from 'lucide-react';
import type {Page, User} from './types';

type NavItem = {id:Page;title:string;icon:LucideIcon};
type Props = {items:NavItem[];page:Page;name:string;city:string;user:User;reviews:number;mobileOpen:boolean;collapsed:boolean;onToggle:()=>void;onNavigate:(page:Page)=>void;onLogout:()=>void};

export default function Sidebar({items,page,name,city,user,reviews,mobileOpen,collapsed,onToggle,onNavigate,onLogout}:Props){
  const [accountOpen,setAccountOpen]=useState(false);
  const account=useRef<HTMLDivElement>(null);
  useEffect(()=>{
    if(!accountOpen)return;
    function outside(e:PointerEvent){if(!account.current?.contains(e.target as Node))setAccountOpen(false);}
    function escape(e:KeyboardEvent){if(e.key==='Escape')setAccountOpen(false);}
    document.addEventListener('pointerdown',outside);document.addEventListener('keydown',escape);
    return()=>{document.removeEventListener('pointerdown',outside);document.removeEventListener('keydown',escape);};
  },[accountOpen]);
  function navigate(target:Page){setAccountOpen(false);onNavigate(target);}
  return <aside className={'sidebar '+(mobileOpen?'open':'')} aria-label="Navigation de l’application">
    <div className="sidebar-header">
      <a href="#dashboard" className="sidebar-project" title={name} onClick={()=>navigate('dashboard')}>
        <span className="project-symbol"><Recycle size={21} strokeWidth={1.8}/></span>
        <span className="project-label"><strong>{name}</strong><small>{city}</small></span>
      </a>
      <button className="sidebar-toggle icon-button" aria-label={collapsed?'Développer la navigation':'Réduire la navigation'} title={collapsed?'Développer la navigation':'Réduire la navigation'} onClick={onToggle}>{collapsed?<PanelLeftOpen size={17}/>:<PanelLeftClose size={17}/>}</button>
    </div>
    <nav aria-label="Navigation principale">
      {[{label:'Navigation',links:items.slice(0,5)},{label:'Configuration',links:items.slice(5)}].map(section=><div className="nav-group" key={section.label}>
        <div className="nav-group-label">{section.label}</div>
        {section.links.map(item=><a key={item.id} href={'#'+item.id} className={'nav-item '+(page===item.id?'active':'')} aria-label={item.title} aria-current={page===item.id?'page':undefined} title={collapsed?item.title:undefined} onClick={()=>navigate(item.id)}>
          <item.icon size={19} strokeWidth={1.8}/><span className="nav-text">{item.title}</span>
          {item.id==='reviews'&&reviews>0&&<small className="nav-count" aria-label={reviews+' vérifications en attente'}>{reviews}</small>}
        </a>)}
      </div>)}
    </nav>
    <div className="sidebar-account" ref={account}>
      {accountOpen&&<div className="account-popover" id="account-actions"><button onClick={()=>navigate('settings')}><Settings size={16}/>Mon compte</button><button onClick={()=>{setAccountOpen(false);onLogout();}}><LogOut size={16}/>Se déconnecter</button></div>}
      <button className="profile-button" onClick={()=>setAccountOpen(!accountOpen)} aria-expanded={accountOpen} aria-controls="account-actions" title={collapsed?user.name:undefined}>
        <span className="avatar">{user.name.split(' ').map(x=>x[0]).slice(0,2).join('').toUpperCase()}</span>
        <span className="profile-label">{user.name}<small>{user.role==='admin'?'Administrateur':user.role==='agent'?'Agent':'Vérificateur'}</small></span><ChevronUp className="profile-chevron" size={15}/>
      </button>
    </div>
  </aside>;
}
