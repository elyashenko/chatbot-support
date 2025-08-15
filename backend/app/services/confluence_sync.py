import aiohttp
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from ..core.config import settings
from ..models.rag_engine import rag_pipeline


class ConfluenceSync:
    """Сервис для синхронизации документации из Confluence"""
    
    def __init__(self):
        self.base_url = settings.confluence_url
        self.username = settings.confluence_username
        self.api_token = settings.confluence_api_token
        self.space_keys = settings.confluence_space_keys
    
    async def sync_all_spaces(self) -> Dict[str, Any]:
        """Синхронизирует все настроенные пространства"""
        if not all([self.base_url, self.username, self.api_token]):
            logger.warning("Confluence credentials not configured")
            return {"success": False, "error": "Confluence credentials not configured"}
        
        try:
            all_documents = []
            
            for space_key in self.space_keys:
                logger.info(f"Синхронизация пространства: {space_key}")
                space_documents = await self._sync_space(space_key)
                all_documents.extend(space_documents)
            
            if all_documents:
                # Добавляем документы в векторную базу
                doc_ids = await rag_pipeline.add_knowledge_documents(all_documents)
                logger.info(f"Добавлено {len(doc_ids)} документов в базу знаний")
            
            return {
                "success": True,
                "documents_synced": len(all_documents),
                "spaces_synced": len(self.space_keys)
            }
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации Confluence: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _sync_space(self, space_key: str) -> List[Dict[str, Any]]:
        """Синхронизирует конкретное пространство"""
        documents = []
        
        try:
            # Получаем список страниц в пространстве
            pages = await self._get_space_pages(space_key)
            
            for page in pages:
                try:
                    # Получаем содержимое страницы
                    content = await self._get_page_content(page['id'])
                    
                    if content:
                        document = {
                            "text": content,
                            "metadata": {
                                "title": page.get('title', ''),
                                "source_type": "confluence",
                                "source_url": f"{self.base_url}/wiki{page.get('_links', {}).get('webui', '')}",
                                "space_key": space_key,
                                "page_id": page['id'],
                                "created_at": page.get('created', ''),
                                "updated_at": page.get('updated', '')
                            }
                        }
                        documents.append(document)
                        
                except Exception as e:
                    logger.error(f"Ошибка получения содержимого страницы {page['id']}: {str(e)}")
                    continue
            
            logger.info(f"Синхронизировано {len(documents)} документов из пространства {space_key}")
            return documents
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации пространства {space_key}: {str(e)}")
            return []
    
    async def _get_space_pages(self, space_key: str) -> List[Dict[str, Any]]:
        """Получает список страниц в пространстве"""
        headers = self._get_auth_headers()
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/rest/api/space/{space_key}/content"
            params = {
                "type": "page",
                "status": "current",
                "expand": "version,space"
            }
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('results', [])
                else:
                    raise Exception(f"Failed to get space pages: {response.status}")
    
    async def _get_page_content(self, page_id: str) -> Optional[str]:
        """Получает содержимое страницы"""
        headers = self._get_auth_headers()
        
        async with aiohttp.ClientSession() as session:
            url = f"{self.base_url}/rest/api/content/{page_id}"
            params = {
                "expand": "body.storage"
            }
            
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    body = data.get('body', {}).get('storage', {})
                    return body.get('value', '')
                else:
                    raise Exception(f"Failed to get page content: {response.status}")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """Возвращает заголовки авторизации"""
        import base64
        auth_string = f"{self.username}:{self.api_token}"
        auth_bytes = auth_string.encode('ascii')
        auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
        
        return {
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/json"
        }
    
    async def get_space_info(self, space_key: str) -> Dict[str, Any]:
        """Получает информацию о пространстве"""
        if not all([self.base_url, self.username, self.api_token]):
            return {"error": "Confluence credentials not configured"}
        
        try:
            headers = self._get_auth_headers()
            
            async with aiohttp.ClientSession() as session:
                url = f"{self.base_url}/rest/api/space/{space_key}"
                
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"Failed to get space info: {response.status}"}
                        
        except Exception as e:
            logger.error(f"Ошибка получения информации о пространстве: {str(e)}")
            return {"error": str(e)}


# Глобальный экземпляр сервиса
confluence_sync = ConfluenceSync()
