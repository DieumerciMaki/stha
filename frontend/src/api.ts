export class ApiError extends Error {
  status:number;
  constructor(message:string,status:number){super(message);this.status=status;}
}
export async function api<T>(path:string, options:RequestInit={}):Promise<T> {
  const response=await fetch('/api'+path,{...options,credentials:'same-origin'});
  if(!response.ok){
    let message='Le serveur ne peut pas traiter cette demande.';
    try{const data=await response.json();message=typeof data.detail==='string'?data.detail:'Vérifiez les champs du formulaire.';}catch{ /* Keep network-safe message. */ }
    throw new ApiError(message,response.status);
  }
  return response.json();
}
export function json(method:string,body:unknown):RequestInit{return {method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)};}
export const dateLabel=(value:string|null)=>value?new Date(value.length===10?value+'T12:00:00':value).toLocaleDateString('fr-FR'):'—';
export const numberLabel=(value:number,maximumFractionDigits=1)=>value.toLocaleString('fr-FR',{maximumFractionDigits});
