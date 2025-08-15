import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import json
import uuid
from loguru import logger
from ..core.config import settings
from .embeddings import embedding_model


class ChromaVectorStore:
    """Класс для работы с векторной базой данных Chroma"""
    
    def __init__(self, persist_directory: str = None):
        self.persist_directory = persist_directory or settings.chroma_persist_directory
        self.client = None
        self.collection = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Инициализирует клиент Chroma"""
        try:
            logger.info(f"Инициализация Chroma клиента: {self.persist_directory}")
            
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # Создаем или получаем коллекцию
            self.collection = self.client.get_or_create_collection(
                name="knowledge_base",
                metadata={"description": "База знаний для RAG чат-бота"}
            )
            
            logger.info("Chroma клиент успешно инициализирован")
        except Exception as e:
            logger.error(f"Ошибка инициализации Chroma: {str(e)}")
            raise
    
    def add_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Добавляет документы в векторную базу"""
        try:
            if not documents:
                return []
            
            ids = []
            texts = []
            metadatas = []
            embeddings = []
            
            for doc in documents:
                # Генерируем уникальный ID
                doc_id = str(uuid.uuid4())
                ids.append(doc_id)
                
                # Извлекаем текст
                text = doc.get("text", "")
                texts.append(text)
                
                # Подготавливаем метаданные
                metadata = doc.get("metadata", {}).copy()
                metadata["doc_id"] = doc_id
                metadata["text_length"] = len(text)
                metadatas.append(metadata)
                
                # Генерируем embedding
                embedding = embedding_model.encode_text(text)
                embeddings.append(embedding)
            
            # Добавляем в коллекцию
            self.collection.add(
                ids=ids,
                documents=texts,
                metadatas=metadatas,
                embeddings=embeddings
            )
            
            logger.info(f"Добавлено {len(documents)} документов в векторную базу")
            return ids
        except Exception as e:
            logger.error(f"Ошибка добавления документов: {str(e)}")
            raise
    
    def search_similar(self, query: str, n_results: int = None, 
                      filter_metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Поиск похожих документов"""
        try:
            n_results = n_results or settings.top_k_results
            
            # Генерируем embedding для запроса
            query_embedding = embedding_model.encode_text(query)
            
            # Выполняем поиск
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter_metadata
            )
            
            # Форматируем результаты
            formatted_results = []
            if results["documents"] and results["documents"][0]:
                for i in range(len(results["documents"][0])):
                    formatted_results.append({
                        "id": results["ids"][0][i],
                        "text": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i],
                        "similarity": 1 - results["distances"][0][i]  # Конвертируем расстояние в сходство
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Ошибка поиска в векторной базе: {str(e)}")
            return []
    
    def search_by_metadata(self, filter_metadata: Dict[str, Any], 
                          n_results: int = None) -> List[Dict[str, Any]]:
        """Поиск документов по метаданным"""
        try:
            n_results = n_results or settings.top_k_results
            
            results = self.collection.get(
                where=filter_metadata,
                limit=n_results
            )
            
            formatted_results = []
            if results["documents"]:
                for i in range(len(results["documents"])):
                    formatted_results.append({
                        "id": results["ids"][i],
                        "text": results["documents"][i],
                        "metadata": results["metadatas"][i]
                    })
            
            return formatted_results
        except Exception as e:
            logger.error(f"Ошибка поиска по метаданным: {str(e)}")
            return []
    
    def update_document(self, doc_id: str, new_text: str, 
                       new_metadata: Dict[str, Any] = None) -> bool:
        """Обновляет документ в векторной базе"""
        try:
            # Генерируем новый embedding
            new_embedding = embedding_model.encode_text(new_text)
            
            # Обновляем метаданные
            metadata = new_metadata or {}
            metadata["updated_at"] = str(uuid.uuid4())  # Простой способ отметить обновление
            
            # Обновляем в коллекции
            self.collection.update(
                ids=[doc_id],
                documents=[new_text],
                metadatas=[metadata],
                embeddings=[new_embedding]
            )
            
            logger.info(f"Документ {doc_id} успешно обновлен")
            return True
        except Exception as e:
            logger.error(f"Ошибка обновления документа {doc_id}: {str(e)}")
            return False
    
    def delete_document(self, doc_id: str) -> bool:
        """Удаляет документ из векторной базы"""
        try:
            self.collection.delete(ids=[doc_id])
            logger.info(f"Документ {doc_id} успешно удален")
            return True
        except Exception as e:
            logger.error(f"Ошибка удаления документа {doc_id}: {str(e)}")
            return False
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Возвращает статистику коллекции"""
        try:
            count = self.collection.count()
            return {
                "total_documents": count,
                "collection_name": self.collection.name,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {str(e)}")
            return {}
    
    def reset_collection(self) -> bool:
        """Сбрасывает коллекцию (удаляет все документы)"""
        try:
            self.client.delete_collection(name=self.collection.name)
            self.collection = self.client.create_collection(
                name="knowledge_base",
                metadata={"description": "База знаний для RAG чат-бота"}
            )
            logger.info("Коллекция успешно сброшена")
            return True
        except Exception as e:
            logger.error(f"Ошибка сброса коллекции: {str(e)}")
            return False
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Получает документ по ID"""
        try:
            results = self.collection.get(ids=[doc_id])
            
            if results["documents"]:
                return {
                    "id": results["ids"][0],
                    "text": results["documents"][0],
                    "metadata": results["metadatas"][0]
                }
            return None
        except Exception as e:
            logger.error(f"Ошибка получения документа {doc_id}: {str(e)}")
            return None


class VectorStoreManager:
    """Менеджер для работы с векторной базой данных"""
    
    def __init__(self):
        self.vector_store = ChromaVectorStore()
    
    async def add_knowledge_documents(self, documents: List[Dict[str, Any]]) -> List[str]:
        """Добавляет документы знаний в векторную базу"""
        try:
            # Разбиваем документы на чанки
            from .embeddings import document_chunker
            chunks = document_chunker.chunk_documents(documents)
            
            # Добавляем в векторную базу
            doc_ids = self.vector_store.add_documents(chunks)
            
            logger.info(f"Добавлено {len(doc_ids)} чанков в векторную базу")
            return doc_ids
        except Exception as e:
            logger.error(f"Ошибка добавления документов знаний: {str(e)}")
            raise
    
    async def search_relevant_context(self, query: str, 
                                    filter_metadata: Dict[str, Any] = None,
                                    n_results: int = None) -> List[Dict[str, Any]]:
        """Поиск релевантного контекста для запроса"""
        try:
            results = self.vector_store.search_similar(
                query=query,
                n_results=n_results,
                filter_metadata=filter_metadata
            )
            
            # Фильтруем по порогу сходства
            threshold = settings.similarity_threshold
            filtered_results = [
                result for result in results 
                if result["similarity"] >= threshold
            ]
            
            logger.info(f"Найдено {len(filtered_results)} релевантных документов")
            return filtered_results
        except Exception as e:
            logger.error(f"Ошибка поиска контекста: {str(e)}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Возвращает статистику векторной базы"""
        return self.vector_store.get_collection_stats()


# Глобальный экземпляр менеджера
vector_store_manager = VectorStoreManager()
