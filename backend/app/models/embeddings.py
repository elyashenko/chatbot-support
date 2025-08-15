from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any, Optional
import numpy as np
import json
from loguru import logger
from ..core.config import settings


class EmbeddingModel:
    """Класс для работы с embeddings"""
    
    def __init__(self, model_name: str = None):
        self.model_name = model_name or settings.embedding_model
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Загружает модель embeddings"""
        try:
            logger.info(f"Загрузка модели embeddings: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            logger.info("Модель embeddings успешно загружена")
        except Exception as e:
            logger.error(f"Ошибка загрузки модели embeddings: {str(e)}")
            raise
    
    def encode_text(self, text: str) -> List[float]:
        """Кодирует текст в векторное представление"""
        try:
            if not self.model:
                raise Exception("Модель не загружена")
            
            embedding = self.model.encode(text)
            return embedding.tolist()
        except Exception as e:
            logger.error(f"Ошибка кодирования текста: {str(e)}")
            raise
    
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Кодирует список текстов в векторные представления"""
        try:
            if not self.model:
                raise Exception("Модель не загружена")
            
            embeddings = self.model.encode(texts)
            return embeddings.tolist()
        except Exception as e:
            logger.error(f"Ошибка пакетного кодирования: {str(e)}")
            raise
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """Вычисляет косинусное сходство между двумя векторами"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Нормализация векторов
            vec1_norm = vec1 / np.linalg.norm(vec1)
            vec2_norm = vec2 / np.linalg.norm(vec2)
            
            # Косинусное сходство
            similarity = np.dot(vec1_norm, vec2_norm)
            return float(similarity)
        except Exception as e:
            logger.error(f"Ошибка вычисления сходства: {str(e)}")
            return 0.0
    
    def find_most_similar(self, query_embedding: List[float], 
                         candidate_embeddings: List[List[float]], 
                         top_k: int = 5) -> List[Dict[str, Any]]:
        """Находит наиболее похожие векторы"""
        try:
            similarities = []
            for i, candidate in enumerate(candidate_embeddings):
                similarity = self.calculate_similarity(query_embedding, candidate)
                similarities.append({
                    "index": i,
                    "similarity": similarity
                })
            
            # Сортировка по убыванию сходства
            similarities.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Возвращаем top_k результатов
            return similarities[:top_k]
        except Exception as e:
            logger.error(f"Ошибка поиска похожих векторов: {str(e)}")
            return []


class DocumentChunker:
    """Класс для разбиения документов на чанки"""
    
    def __init__(self, chunk_size: int = None, chunk_overlap: int = None):
        self.chunk_size = chunk_size or settings.chunk_size
        self.chunk_overlap = chunk_overlap or settings.chunk_overlap
    
    def chunk_text(self, text: str, metadata: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Разбивает текст на чанки"""
        try:
            chunks = []
            start = 0
            
            while start < len(text):
                end = start + self.chunk_size
                chunk_text = text[start:end]
                
                # Создаем метаданные для чанка
                chunk_metadata = {
                    "start_pos": start,
                    "end_pos": end,
                    "chunk_size": len(chunk_text)
                }
                
                if metadata:
                    chunk_metadata.update(metadata)
                
                chunks.append({
                    "text": chunk_text,
                    "metadata": chunk_metadata
                })
                
                # Переходим к следующему чанку с перекрытием
                start = end - self.chunk_overlap
                
                # Избегаем бесконечного цикла
                if start >= len(text):
                    break
            
            return chunks
        except Exception as e:
            logger.error(f"Ошибка разбиения текста на чанки: {str(e)}")
            return []
    
    def chunk_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Разбивает список документов на чанки"""
        try:
            all_chunks = []
            
            for doc in documents:
                text = doc.get("content", "")
                metadata = doc.get("metadata", {})
                
                chunks = self.chunk_text(text, metadata)
                all_chunks.extend(chunks)
            
            return all_chunks
        except Exception as e:
            logger.error(f"Ошибка разбиения документов: {str(e)}")
            return []


class HybridSearch:
    """Класс для гибридного поиска (векторный + keyword)"""
    
    def __init__(self, embedding_model: EmbeddingModel):
        self.embedding_model = embedding_model
    
    def keyword_search(self, query: str, documents: List[Dict[str, Any]], 
                      top_k: int = 5) -> List[Dict[str, Any]]:
        """Простой keyword поиск"""
        try:
            query_words = set(query.lower().split())
            scored_docs = []
            
            for doc in documents:
                text = doc.get("text", "").lower()
                doc_words = set(text.split())
                
                # Вычисляем пересечение слов
                intersection = query_words.intersection(doc_words)
                score = len(intersection) / len(query_words) if query_words else 0
                
                scored_docs.append({
                    "document": doc,
                    "keyword_score": score
                })
            
            # Сортировка по убыванию score
            scored_docs.sort(key=lambda x: x["keyword_score"], reverse=True)
            return scored_docs[:top_k]
        except Exception as e:
            logger.error(f"Ошибка keyword поиска: {str(e)}")
            return []
    
    def hybrid_search(self, query: str, documents: List[Dict[str, Any]], 
                     vector_weight: float = 0.7, top_k: int = 5) -> List[Dict[str, Any]]:
        """Гибридный поиск: комбинация векторного и keyword поиска"""
        try:
            # Векторный поиск
            query_embedding = self.embedding_model.encode_text(query)
            doc_embeddings = [self.embedding_model.encode_text(doc.get("text", "")) 
                            for doc in documents]
            
            vector_results = self.embedding_model.find_most_similar(
                query_embedding, doc_embeddings, top_k * 2
            )
            
            # Keyword поиск
            keyword_results = self.keyword_search(query, documents, top_k * 2)
            
            # Объединяем результаты
            combined_scores = {}
            
            # Добавляем векторные результаты
            for result in vector_results:
                doc_index = result["index"]
                doc = documents[doc_index]
                doc_id = doc.get("metadata", {}).get("id", doc_index)
                
                if doc_id not in combined_scores:
                    combined_scores[doc_id] = {
                        "document": doc,
                        "vector_score": result["similarity"],
                        "keyword_score": 0.0,
                        "combined_score": 0.0
                    }
                else:
                    combined_scores[doc_id]["vector_score"] = result["similarity"]
            
            # Добавляем keyword результаты
            for result in keyword_results:
                doc = result["document"]
                doc_id = doc.get("metadata", {}).get("id", hash(str(doc)))
                
                if doc_id not in combined_scores:
                    combined_scores[doc_id] = {
                        "document": doc,
                        "vector_score": 0.0,
                        "keyword_score": result["keyword_score"],
                        "combined_score": 0.0
                    }
                else:
                    combined_scores[doc_id]["keyword_score"] = result["keyword_score"]
            
            # Вычисляем комбинированный score
            for doc_id, scores in combined_scores.items():
                combined_score = (vector_weight * scores["vector_score"] + 
                                (1 - vector_weight) * scores["keyword_score"])
                scores["combined_score"] = combined_score
            
            # Сортировка по комбинированному score
            final_results = list(combined_scores.values())
            final_results.sort(key=lambda x: x["combined_score"], reverse=True)
            
            return final_results[:top_k]
        except Exception as e:
            logger.error(f"Ошибка гибридного поиска: {str(e)}")
            return []


# Глобальные экземпляры
embedding_model = EmbeddingModel()
document_chunker = DocumentChunker()
hybrid_search = HybridSearch(embedding_model)
