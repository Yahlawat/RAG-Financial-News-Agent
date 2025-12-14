"""Tests for the RAG chain."""

import pytest
from unittest.mock import MagicMock, patch

from finnews.rag.rag_chain import format_doc_with_metadata, rag_chat


class TestFormatDocWithMetadata:
    """Test document formatting for LLM context."""

    def test_format_chat_document(self):
        """Test formatting of chat history documents."""
        doc = MagicMock()
        doc.page_content = "What is the latest news about AAPL?"
        doc.metadata = {"role": "user"}

        result = format_doc_with_metadata(doc, doc_type="chat")

        assert result == "[USER]: What is the latest news about AAPL?"

    def test_format_news_document_with_tickers(self):
        """Test formatting of news documents with ticker information."""
        doc = MagicMock()
        doc.page_content = "Apple reports strong Q4 earnings."
        doc.metadata = {
            "title": "Apple Q4 Earnings",
            "published_date": "2024-01-01",
            "relevant_tickers": "AAPL, MSFT",
        }

        result = format_doc_with_metadata(doc, doc_type="news")

        assert "[Article: Apple Q4 Earnings (AAPL, MSFT) - 2024-01-01]" in result
        assert "Apple reports strong Q4 earnings." in result

    def test_format_news_document_no_tickers(self):
        """Test formatting of news documents without tickers."""
        doc = MagicMock()
        doc.page_content = "Market analysis shows positive trends."
        doc.metadata = {
            "title": "Market Analysis",
            "published_date": "2024-01-02",
            "relevant_tickers": "",
        }

        result = format_doc_with_metadata(doc, doc_type="news")

        assert "[Article: Market Analysis - 2024-01-02]" in result
        assert "Market analysis shows positive trends." in result
        # Should not have empty parentheses for tickers
        assert "()" not in result


class TestRagChat:
    """Test the core RAG chat functionality."""

    @patch("finnews.rag.rag_chain.ChatOpenAI")
    @patch("finnews.rag.rag_chain.retrieve_chat_memory")
    @patch("finnews.rag.rag_chain.article_chunk_retriever")
    @patch("finnews.rag.rag_chain.add_chat_memory")
    def test_rag_chat_basic_question(
        self, mock_add_memory, mock_retriever, mock_chat_memory, mock_openai
    ):
        """Test basic question answering flow."""
        # Setup mocks
        mock_chat_memory.return_value = []  # No chat history

        # Mock article retrieval
        mock_doc = MagicMock()
        mock_doc.page_content = "Apple reported Q4 earnings of $89.5 billion."
        mock_doc.metadata = {
            "title": "Apple Q4 Earnings",
            "url": "https://example.com/apple-earnings",
            "published_date": "2024-01-01",
            "relevant_tickers": "AAPL",
        }
        mock_retriever.return_value = [mock_doc]

        # Mock LLM response
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Apple reported strong Q4 earnings of $89.5 billion."
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance

        # Create mock vector stores
        article_store = MagicMock()
        chat_store = MagicMock()

        # Execute
        result = rag_chat(
            question="What is the latest news about AAPL?",
            conversation_id="test_conv",
            user_id="test_user",
            article_store=article_store,
            chat_store=chat_store,
        )

        # Verify response structure
        assert result["conversation_id"] == "test_conv"
        assert result["user_id"] == "test_user"
        assert result["question"] == "What is the latest news about AAPL?"
        assert "89.5 billion" in result["answer"]
        assert len(result["sources"]) == 1
        assert result["sources"][0]["title"] == "Apple Q4 Earnings"
        assert result["sources"][0]["url"] == "https://example.com/apple-earnings"

        # Verify memory was saved
        mock_add_memory.assert_called_once()

    @patch("finnews.rag.rag_chain.ChatOpenAI")
    @patch("finnews.rag.rag_chain.retrieve_chat_memory")
    @patch("finnews.rag.rag_chain.article_chunk_retriever")
    @patch("finnews.rag.rag_chain.add_chat_memory")
    def test_rag_chat_with_conversation_history(
        self, mock_add_memory, mock_retriever, mock_chat_memory, mock_openai
    ):
        """Test that conversation history is included in context."""
        # Setup chat history
        history_doc = MagicMock()
        history_doc.page_content = "What happened with Microsoft?"
        history_doc.metadata = {"role": "user"}
        mock_chat_memory.return_value = [history_doc]

        # Mock article retrieval
        mock_doc = MagicMock()
        mock_doc.page_content = "Microsoft acquired Activision for $69 billion."
        mock_doc.metadata = {
            "title": "Microsoft Acquisition",
            "url": "https://example.com/msft",
            "published_date": "2024-01-01",
            "relevant_tickers": "MSFT",
        }
        mock_retriever.return_value = [mock_doc]

        # Mock LLM response
        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Microsoft completed the Activision acquisition."
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance

        article_store = MagicMock()
        chat_store = MagicMock()

        # Execute
        result = rag_chat(
            question="Tell me more about it",
            conversation_id="test_conv",
            user_id="test_user",
            article_store=article_store,
            chat_store=chat_store,
        )

        # Verify chat memory was retrieved
        mock_chat_memory.assert_called_once()

        # Verify the answer references context
        assert "Microsoft" in result["answer"]

    @patch("finnews.rag.rag_chain.ChatOpenAI")
    @patch("finnews.rag.rag_chain.retrieve_chat_memory")
    @patch("finnews.rag.rag_chain.article_chunk_retriever")
    @patch("finnews.rag.rag_chain.add_chat_memory")
    def test_rag_chat_ticker_filtering(
        self, mock_add_memory, mock_retriever, mock_chat_memory, mock_openai
    ):
        """Test that ticker filtering is passed to retriever."""
        mock_chat_memory.return_value = []

        mock_doc = MagicMock()
        mock_doc.page_content = "Tesla stock rises 5%."
        mock_doc.metadata = {
            "title": "Tesla News",
            "url": "https://example.com/tsla",
            "published_date": "2024-01-01",
            "relevant_tickers": "TSLA",
        }
        mock_retriever.return_value = [mock_doc]

        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Tesla stock increased by 5%."
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance

        article_store = MagicMock()
        chat_store = MagicMock()

        # Execute with ticker filter
        result = rag_chat(
            question="What's happening with Tesla?",
            conversation_id="test_conv",
            user_id="test_user",
            target_tickers=["TSLA"],
            article_store=article_store,
            chat_store=chat_store,
        )

        # Verify ticker filtering was used
        mock_retriever.assert_called_once()
        call_kwargs = mock_retriever.call_args[1]
        assert call_kwargs["target_tickers"] == ["TSLA"]

    @patch("finnews.rag.rag_chain.ChatOpenAI")
    @patch("finnews.rag.rag_chain.retrieve_chat_memory")
    @patch("finnews.rag.rag_chain.article_chunk_retriever")
    @patch("finnews.rag.rag_chain.add_chat_memory")
    def test_rag_chat_no_sources(
        self, mock_add_memory, mock_retriever, mock_chat_memory, mock_openai
    ):
        """Test handling when no relevant articles are found."""
        mock_chat_memory.return_value = []
        mock_retriever.return_value = []  # No articles found

        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "I don't have information about that topic."
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance

        article_store = MagicMock()
        chat_store = MagicMock()

        result = rag_chat(
            question="What is the weather?",
            conversation_id="test_conv",
            user_id="test_user",
            article_store=article_store,
            chat_store=chat_store,
        )

        # Should return response with empty sources
        assert result["sources"] == []
        assert "information" in result["answer"].lower()

    @patch("finnews.rag.rag_chain.retrieve_chat_memory")
    @patch("finnews.rag.rag_chain.article_chunk_retriever")
    def test_rag_chat_missing_api_key(self, mock_retriever, mock_chat_memory):
        """Test that missing OpenAI API key raises appropriate error."""
        mock_chat_memory.return_value = []
        mock_retriever.return_value = []

        article_store = MagicMock()
        chat_store = MagicMock()

        with patch("finnews.rag.rag_chain.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            mock_settings.LLM_MODEL = "gpt-4o-mini"

            with patch.dict("os.environ", {}, clear=True):
                with pytest.raises(ValueError, match="OPENAI_API_KEY is required"):
                    rag_chat(
                        question="Test question",
                        conversation_id="test_conv",
                        user_id="test_user",
                        article_store=article_store,
                        chat_store=chat_store,
                    )

    @patch("finnews.rag.rag_chain.ChatOpenAI")
    @patch("finnews.rag.rag_chain.retrieve_chat_memory")
    @patch("finnews.rag.rag_chain.article_chunk_retriever")
    @patch("finnews.rag.rag_chain.add_chat_memory")
    def test_rag_chat_llm_failure(
        self, mock_add_memory, mock_retriever, mock_chat_memory, mock_openai
    ):
        """Test handling of LLM API failures."""
        mock_chat_memory.return_value = []
        mock_retriever.return_value = []

        # Mock LLM to raise exception
        mock_llm_instance = MagicMock()
        mock_llm_instance.invoke.side_effect = Exception("OpenAI API error")
        mock_openai.return_value = mock_llm_instance

        article_store = MagicMock()
        chat_store = MagicMock()

        with pytest.raises(Exception, match="OpenAI API error"):
            rag_chat(
                question="Test question",
                conversation_id="test_conv",
                user_id="test_user",
                article_store=article_store,
                chat_store=chat_store,
            )

        # Memory should NOT be saved when LLM fails
        mock_add_memory.assert_not_called()

    @patch("finnews.rag.rag_chain.ChatOpenAI")
    @patch("finnews.rag.rag_chain.retrieve_chat_memory")
    @patch("finnews.rag.rag_chain.article_chunk_retriever")
    @patch("finnews.rag.rag_chain.add_chat_memory")
    def test_rag_chat_source_deduplication(
        self, mock_add_memory, mock_retriever, mock_chat_memory, mock_openai
    ):
        """Test that sources from same article are properly handled."""
        mock_chat_memory.return_value = []

        # Mock multiple chunks from same article
        doc1 = MagicMock()
        doc1.page_content = "First chunk about Apple."
        doc1.metadata = {
            "title": "Apple News",
            "url": "https://example.com/apple",
            "published_date": "2024-01-01",
            "relevant_tickers": "AAPL",
        }

        doc2 = MagicMock()
        doc2.page_content = "Second chunk about Apple."
        doc2.metadata = {
            "title": "Apple News",
            "url": "https://example.com/apple",  # Same URL
            "published_date": "2024-01-01",
            "relevant_tickers": "AAPL",
        }

        mock_retriever.return_value = [doc1, doc2]

        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Apple news summary."
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance

        article_store = MagicMock()
        chat_store = MagicMock()

        result = rag_chat(
            question="What about Apple?",
            conversation_id="test_conv",
            user_id="test_user",
            article_store=article_store,
            chat_store=chat_store,
        )

        # Should include sources even if duplicates (UI can handle deduplication)
        # This tests that we extract sources correctly
        assert len(result["sources"]) == 2
        assert all(s["url"] == "https://example.com/apple" for s in result["sources"])

    @patch("finnews.rag.rag_chain.load_vectorstore")
    @patch("finnews.rag.rag_chain.ChatOpenAI")
    @patch("finnews.rag.rag_chain.retrieve_chat_memory")
    @patch("finnews.rag.rag_chain.article_chunk_retriever")
    @patch("finnews.rag.rag_chain.add_chat_memory")
    def test_rag_chat_auto_load_vector_stores(
        self, mock_add_memory, mock_retriever, mock_chat_memory, mock_openai, mock_load_vs
    ):
        """Test that vector stores are auto-loaded when not provided."""
        mock_chat_memory.return_value = []
        mock_retriever.return_value = []

        mock_llm_instance = MagicMock()
        mock_response = MagicMock()
        mock_response.content = "Test response."
        mock_llm_instance.invoke.return_value = mock_response
        mock_openai.return_value = mock_llm_instance

        mock_vs = MagicMock()
        mock_load_vs.return_value = mock_vs

        # Call without providing vector stores
        result = rag_chat(
            question="Test question",
            conversation_id="test_conv",
            user_id="test_user",
            # article_store and chat_store not provided
        )

        # Verify vector stores were loaded
        assert mock_load_vs.call_count == 2  # Once for articles, once for chat
