export type LanguageCode='en-NG'|'yo-NG'|'ha-NG'|'ig-NG'|'pcm-NG';
export interface AccessibilityProfile{primary_language:LanguageCode;allow_code_switching:boolean;voice_guidance:boolean;captions:boolean;screen_reader:boolean;large_text:boolean;high_contrast:boolean;large_targets:boolean;switch_control:boolean;extended_timeout:boolean;easy_banking:boolean;reduced_motion:boolean}
export interface AssistantRequest{text:string;language_hint?:LanguageCode;interaction_mode?:'text'|'voice'|'quick_action'|'switch'}
export interface BankingIntent{intent_id:string;action:string;language:LanguageCode;code_switched:boolean;amount?:number|null;beneficiary_query?:string|null;transaction_query?:string|null;confidence:number;clarification?:string|null}
export interface AssistantResponse{type:'message'|'transfer_preview'|'confirmation'|'error';intent:BankingIntent;message:string;data:Record<string,unknown>}
export interface AccessFlowOptions{baseUrl:string;token?:string;fetchImpl?:typeof fetch;onEvent?:(name:string,payload?:unknown)=>void}

/** Browser SDK intended to be embedded inside an existing bank application. It does not own customer identity or core banking state. */
export class AccessFlow{
  private baseUrl:string;private token?:string;private f:typeof fetch;private onEvent?:(name:string,payload?:unknown)=>void;
  constructor(options:AccessFlowOptions|string,token?:string){if(typeof options==='string'){this.baseUrl=options.replace(/\/$/,'');this.token=token;this.f=fetch;return}this.baseUrl=options.baseUrl.replace(/\/$/,'');this.token=options.token;this.f=options.fetchImpl||fetch;this.onEvent=options.onEvent}
  private async request<T>(path:string,init:RequestInit={}):Promise<T>{const headers=new Headers(init.headers||{});headers.set('Content-Type','application/json');if(this.token)headers.set('Authorization',`Bearer ${this.token}`);const r=await this.f(`${this.baseUrl}/api/v1${path}`,{...init,headers});const data=await r.json().catch(()=>({detail:r.statusText}));if(!r.ok)throw new Error(data.detail||r.statusText);return data as T}
  private emit(n:string,p?:unknown){this.onEvent?.(n,p)}
  getLanguages(){return this.request<Array<{code:LanguageCode;name:string;native:string}>>('/languages')}
  getProfile(){return this.request<AccessibilityProfile>('/profile')}
  async saveProfile(profile:AccessibilityProfile){const out=await this.request<AccessibilityProfile>('/profile',{method:'PUT',body:JSON.stringify(profile)});this.emit('profile_saved',out);return out}
  getAccount(){return this.request('/account')}
  getTransactions(){return this.request('/transactions')}
  getCard(){return this.request('/card')}
  parseIntent(text:string,language_hint?:LanguageCode,interaction_mode='text'){return this.request<BankingIntent>('/intent/parse',{method:'POST',body:JSON.stringify({text,language_hint,interaction_mode})})}
  async assist(input:AssistantRequest|string){const body=typeof input==='string'?{text:input}:input;const out=await this.request<AssistantResponse>('/assistant',{method:'POST',body:JSON.stringify(body)});this.emit('assistant_response',out);return out}
  previewTransfer(intent_id:string){return this.request('/transfers/preview',{method:'POST',body:JSON.stringify({intent_id})})}
  confirmTransfer(preview_id:string,pin:string,idempotency_key?:string){return this.request(`/transfers/${preview_id}/confirm`,{method:'POST',body:JSON.stringify({confirmed:true,pin,idempotency_key})})}
  freezeCard(pin:string){return this.request('/card/freeze',{method:'POST',body:JSON.stringify({confirmed:true,pin})})}
  recordEvent(event:string,payload:Record<string,unknown>={}){return this.request('/events',{method:'POST',body:JSON.stringify({event,...payload})})}
}
