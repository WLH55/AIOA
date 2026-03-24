/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.ai.knowledge;

import com.aiwork.helper.config.DashScopeProperties;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;
import io.lettuce.core.RedisClient;
import io.lettuce.core.api.StatefulRedisConnection;
import io.lettuce.core.api.sync.RedisCommands;
import io.lettuce.core.codec.ByteArrayCodec;
import io.lettuce.core.output.ArrayOutput;
import io.lettuce.core.output.StatusOutput;
import io.lettuce.core.codec.StringCodec;
import io.lettuce.core.protocol.CommandArgs;
import io.lettuce.core.protocol.ProtocolKeyword;
import jakarta.annotation.PostConstruct;
import jakarta.annotation.PreDestroy;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.data.redis.connection.RedisConnection;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 向量存储服务
 * 对应Go版本: getKnowledgeStore使用的Redis Vector Store
 *
 * 功能:
 * - 文本向量化(使用DashScope Embedding API)
 * - 向量存储(使用Redis + RediSearch向量索引)
 * - 相似度检索(使用RediSearch FT.SEARCH进行KNN搜索)
 */
@Slf4j
@Service
public class VectorStoreService {

    private final DashScopeProperties dashScopeProperties;
    private final ObjectMapper objectMapper;
    private final StringRedisTemplate redisTemplate;
    private final RestTemplate restTemplate = new RestTemplate();

    /**
     * Lettuce 原生连接（用于执行 RediSearch 命令）
     */
    private RedisClient lettuceClient;
    private StatefulRedisConnection<byte[], byte[]> lettuceConnection;

    @Value("${spring.data.redis.host:127.0.0.1}")
    private String redisHost;

    @Value("${spring.data.redis.port:6379}")
    private int redisPort;

    /**
     * Redis 向量索引配置（Java 版本独立索引）
     */
    private static final String INDEX_NAME = "knowledge_java";
    private static final String DOC_PREFIX = "doc:knowledge_java:";
    private static final int VECTOR_DIM = 1024;

    public VectorStoreService(DashScopeProperties dashScopeProperties,
                              ObjectMapper objectMapper,
                              StringRedisTemplate redisTemplate) {
        this.dashScopeProperties = dashScopeProperties;
        this.objectMapper = objectMapper;
        this.redisTemplate = redisTemplate;
    }

    /**
     * 初始化 Lettuce 连接和向量索引
     */
    @PostConstruct
    public void init() {
        // 创建 Lettuce 客户端（用于执行 RediSearch 命令）
        String redisUri = String.format("redis://%s:%d", redisHost, redisPort);
        lettuceClient = RedisClient.create(redisUri);
        lettuceConnection = lettuceClient.connect(ByteArrayCodec.INSTANCE);
        log.info("Lettuce 连接创建成功: {}", redisUri);

        createIndexIfNotExists();
    }

    /**
     * 关闭 Lettuce 连接
     */
    @PreDestroy
    public void destroy() {
        if (lettuceConnection != null) {
            lettuceConnection.close();
        }
        if (lettuceClient != null) {
            lettuceClient.shutdown();
        }
        log.info("Lettuce 连接已关闭");
    }

    /**
     * 创建 Redis 向量索引（如果不存在）
     */
    private void createIndexIfNotExists() {
        try {
            RedisCommands<byte[], byte[]> commands = lettuceConnection.sync();

            // 检查索引是否存在
            try {
                CommandArgs<byte[], byte[]> infoArgs = new CommandArgs<>(ByteArrayCodec.INSTANCE)
                        .add(INDEX_NAME.getBytes(StandardCharsets.UTF_8));
                commands.dispatch(RediSearchCommand.FT_INFO, new ArrayOutput<>(ByteArrayCodec.INSTANCE), infoArgs);
                log.info("Redis 向量索引 {} 已存在", INDEX_NAME);
                return;
            } catch (Exception e) {
                // 索引不存在，继续创建
                log.info("索引 {} 不存在，开始创建", INDEX_NAME);
            }

            // 创建索引
            CommandArgs<byte[], byte[]> createArgs = new CommandArgs<>(ByteArrayCodec.INSTANCE)
                    .add(INDEX_NAME.getBytes(StandardCharsets.UTF_8))
                    .add("ON".getBytes(StandardCharsets.UTF_8))
                    .add("HASH".getBytes(StandardCharsets.UTF_8))
                    .add("PREFIX".getBytes(StandardCharsets.UTF_8))
                    .add("1".getBytes(StandardCharsets.UTF_8))
                    .add(DOC_PREFIX.getBytes(StandardCharsets.UTF_8))
                    .add("SCHEMA".getBytes(StandardCharsets.UTF_8))
                    .add("content".getBytes(StandardCharsets.UTF_8))
                    .add("TEXT".getBytes(StandardCharsets.UTF_8))
                    .add("source".getBytes(StandardCharsets.UTF_8))
                    .add("TEXT".getBytes(StandardCharsets.UTF_8))
                    .add("page".getBytes(StandardCharsets.UTF_8))
                    .add("NUMERIC".getBytes(StandardCharsets.UTF_8))
                    .add("content_vector".getBytes(StandardCharsets.UTF_8))
                    .add("VECTOR".getBytes(StandardCharsets.UTF_8))
                    .add("FLAT".getBytes(StandardCharsets.UTF_8))
                    .add("6".getBytes(StandardCharsets.UTF_8))
                    .add("TYPE".getBytes(StandardCharsets.UTF_8))
                    .add("FLOAT32".getBytes(StandardCharsets.UTF_8))
                    .add("DIM".getBytes(StandardCharsets.UTF_8))
                    .add(String.valueOf(VECTOR_DIM).getBytes(StandardCharsets.UTF_8))
                    .add("DISTANCE_METRIC".getBytes(StandardCharsets.UTF_8))
                    .add("COSINE".getBytes(StandardCharsets.UTF_8));

            commands.dispatch(RediSearchCommand.FT_CREATE, new ArrayOutput<>(ByteArrayCodec.INSTANCE), createArgs);
            log.info("Redis 向量索引 {} 创建成功", INDEX_NAME);
        } catch (Exception e) {
            log.warn("创建 Redis 向量索引失败（可能已存在）: {}", e.getMessage());
        }
    }

    /**
     * 添加文档到向量库
     * 对应Go版本: store.AddDocuments
     * 如果同一来源的文档已存在，则先删除旧文档再添加新文档
     *
     * @param chunks 文档块列表
     */
    public void addDocuments(List<PDFProcessor.DocumentChunk> chunks) throws Exception {
        if (chunks.isEmpty()) {
            log.warn("文档块列表为空，跳过添加");
            return;
        }

        // 获取文档来源（所有 chunk 来源相同）
        String source = chunks.get(0).getSource();
        log.info("开始添加 {} 个文档块到 Redis 向量库，来源: {}", chunks.size(), source);

        // 先删除同一来源的旧文档（实现覆盖更新）
        int deletedCount = deleteBySource(source);
        if (deletedCount > 0) {
            log.info("已删除来源 {} 的 {} 个旧文档", source, deletedCount);
        }

        RedisCommands<byte[], byte[]> commands = lettuceConnection.sync();

        for (PDFProcessor.DocumentChunk chunk : chunks) {
            // 1. 生成文档向量
            float[] embedding = generateEmbedding(chunk.getContent());

            // 2. 生成文档 ID
            String docId = DOC_PREFIX + UUID.randomUUID().toString();

            // 3. 将向量转换为二进制格式
            byte[] vectorBytes = floatArrayToBytes(embedding);

            // 4. 存储到 Redis Hash（使用 Lettuce 原生命令）
            String content = chunk.getContent();
            String chunkSource = chunk.getSource();
            int page = chunk.getChunkIndex();

            // 使用 HashMap 构建字段（因为 byte[] 不能直接用于 Map.of）
            java.util.Map<byte[], byte[]> fields = new java.util.HashMap<>();
            fields.put("content".getBytes(StandardCharsets.UTF_8), content.getBytes(StandardCharsets.UTF_8));
            fields.put("source".getBytes(StandardCharsets.UTF_8), chunkSource.getBytes(StandardCharsets.UTF_8));
            fields.put("page".getBytes(StandardCharsets.UTF_8), String.valueOf(page).getBytes(StandardCharsets.UTF_8));
            fields.put("content_vector".getBytes(StandardCharsets.UTF_8), vectorBytes);

            commands.hset(docId.getBytes(StandardCharsets.UTF_8), fields);

            log.debug("文档已存储: {}", docId);
        }

        log.info("文档添加完成，当前向量库大小: {}", size());
    }

    /**
     * 根据来源删除文档
     * 用于在更新文档前删除同一来源的旧文档
     *
     * @param source 文档来源（文件路径）
     * @return 删除的文档数量
     */
    public int deleteBySource(String source) {
        int deletedCount = 0;
        try {
            RedisCommands<byte[], byte[]> commands = lettuceConnection.sync();

            // 获取所有文档 key
            List<byte[]> keys = commands.keys((DOC_PREFIX + "*").getBytes(StandardCharsets.UTF_8));
            if (keys == null || keys.isEmpty()) {
                return 0;
            }

            // 遍历检查每个文档的 source 字段
            for (byte[] key : keys) {
                byte[] sourceValue = commands.hget(key, "source".getBytes(StandardCharsets.UTF_8));
                if (sourceValue != null) {
                    String docSource = new String(sourceValue, StandardCharsets.UTF_8);
                    if (source.equals(docSource)) {
                        commands.del(key);
                        deletedCount++;
                    }
                }
            }
        } catch (Exception e) {
            log.error("根据来源删除文档失败: source={}, error={}", source, e.getMessage());
        }
        return deletedCount;
    }

    /**
     * 搜索相似文档
     * 对应Go版本: vectorstores.ToRetriever(k.store, 1)
     *
     * @param query 查询文本
     * @param topK 返回前K个最相似的文档
     * @return 相似文档列表
     */
    public List<StoredDocument> searchSimilar(String query, int topK) throws Exception {
        int currentSize = size();
        log.info("开始向量搜索: query={}, topK={}, 当前向量库大小={}", query, topK, currentSize);

        if (currentSize == 0) {
            log.warn("向量库为空，无法检索");
            return new ArrayList<>();
        }

        // 1. 生成查询向量
        log.info("正在生成查询向量...");
        float[] queryEmbedding = generateEmbedding(query);
        byte[] queryVectorBytes = floatArrayToBytes(queryEmbedding);
        log.info("查询向量生成完成，维度: {}", queryEmbedding.length);

        // 2. 使用 FT.SEARCH 进行向量搜索
        String searchQuery = "*=>[KNN " + topK + " @content_vector $query_vec AS score]";
        log.info("搜索查询: {}", searchQuery);

        try {
            RedisCommands<byte[], byte[]> commands = lettuceConnection.sync();

            CommandArgs<byte[], byte[]> searchArgs = new CommandArgs<>(ByteArrayCodec.INSTANCE)
                    .add(INDEX_NAME.getBytes(StandardCharsets.UTF_8))
                    .add(searchQuery.getBytes(StandardCharsets.UTF_8))
                    .add("PARAMS".getBytes(StandardCharsets.UTF_8))
                    .add("2".getBytes(StandardCharsets.UTF_8))
                    .add("query_vec".getBytes(StandardCharsets.UTF_8))
                    .add(queryVectorBytes)
                    .add("SORTBY".getBytes(StandardCharsets.UTF_8))
                    .add("score".getBytes(StandardCharsets.UTF_8))
                    .add("RETURN".getBytes(StandardCharsets.UTF_8))
                    .add("3".getBytes(StandardCharsets.UTF_8))
                    .add("content".getBytes(StandardCharsets.UTF_8))
                    .add("source".getBytes(StandardCharsets.UTF_8))
                    .add("page".getBytes(StandardCharsets.UTF_8))
                    .add("DIALECT".getBytes(StandardCharsets.UTF_8))
                    .add("2".getBytes(StandardCharsets.UTF_8));

            log.info("执行 FT.SEARCH 命令...");
            List<Object> result = commands.dispatch(RediSearchCommand.FT_SEARCH,
                    new ArrayOutput<>(ByteArrayCodec.INSTANCE), searchArgs);
            log.info("FT.SEARCH 原始结果: {}", result);

            // 3. 解析搜索结果
            List<StoredDocument> results = parseSearchResults(result);
            log.info("解析后的文档数量: {}", results.size());

            for (int i = 0; i < results.size(); i++) {
                StoredDocument doc = results.get(i);
                log.info("检索结果 {}: 内容={}",
                        i + 1,
                        doc.getContent().substring(0, Math.min(100, doc.getContent().length())));
            }

            return results;
        } catch (Exception e) {
            log.error("向量搜索失败: {}", e.getMessage(), e);
            return new ArrayList<>();
        }
    }

    /**
     * 解析 FT.SEARCH 返回的结果
     * 支持 RESP2 和 RESP3 格式
     */
    @SuppressWarnings("unchecked")
    private List<StoredDocument> parseSearchResults(Object result) {
        List<StoredDocument> documents = new ArrayList<>();

        if (result == null) {
            log.warn("搜索结果为 null");
            return documents;
        }

        try {
            List<Object> resultList = (List<Object>) result;
            log.info("结果列表大小: {}", resultList.size());

            if (resultList.isEmpty()) {
                log.warn("结果列表为空");
                return documents;
            }

            // 打印详细的结果结构用于调试
            for (int i = 0; i < Math.min(resultList.size(), 5); i++) {
                Object item = resultList.get(i);
                String itemStr = item instanceof byte[] ? new String((byte[]) item) : String.valueOf(item);
                log.info("结果元素[{}]: type={}, value={}", i, item.getClass().getSimpleName(),
                        itemStr.length() > 100 ? itemStr.substring(0, 100) + "..." : itemStr);
            }

            // 检测是 RESP2 还是 RESP3 格式
            Object firstElement = resultList.get(0);
            String firstStr = firstElement instanceof byte[] ? new String((byte[]) firstElement) : String.valueOf(firstElement);

            // RESP3 格式：第一个元素是 "attributes" 或其他字符串 key
            if (firstStr.equals("attributes") || firstStr.equals("total_results") || firstStr.equals("results")) {
                log.info("检测到 RESP3 格式，使用 Map 解析");
                parseResp3Results(resultList, documents);
            } else {
                // RESP2 格式：第一个元素是匹配数量
                log.info("检测到 RESP2 格式，使用数组解析");
                parseResp2Results(resultList, documents);
            }
        } catch (Exception e) {
            log.error("解析搜索结果失败: {}", e.getMessage(), e);
        }

        log.info("最终解析出 {} 个文档", documents.size());
        return documents;
    }

    /**
     * 解析 RESP2 格式的结果
     */
    @SuppressWarnings("unchecked")
    private void parseResp2Results(List<Object> resultList, List<StoredDocument> documents) {
        // 第一个元素是匹配的文档数量
        Object countObj = resultList.get(0);
        long matchCount = countObj instanceof Long ? (Long) countObj :
                (countObj instanceof byte[] ? Long.parseLong(new String((byte[]) countObj)) : 0);
        log.info("RESP2 搜索匹配数量: {}", matchCount);

        // 之后每两个元素为一组：文档key, [字段列表]
        for (int i = 1; i < resultList.size(); i += 2) {
            if (i + 1 >= resultList.size()) break;

            Object keyObj = resultList.get(i);
            String docKey = keyObj instanceof byte[] ? new String((byte[]) keyObj) : keyObj.toString();

            Object fieldsObj = resultList.get(i + 1);
            if (!(fieldsObj instanceof List)) continue;

            List<Object> fields = (List<Object>) fieldsObj;
            StoredDocument doc = parseDocumentFields(docKey, fields);
            if (doc != null) {
                documents.add(doc);
            }
        }
    }

    /**
     * 解析 RESP3 格式的结果（map 结构）
     */
    @SuppressWarnings("unchecked")
    private void parseResp3Results(List<Object> resultList, List<StoredDocument> documents) {
        // RESP3 返回的是扁平化的 map: [key1, value1, key2, value2, ...]
        // 需要找到 "results" 对应的值
        for (int i = 0; i < resultList.size() - 1; i += 2) {
            Object keyObj = resultList.get(i);
            String key = keyObj instanceof byte[] ? new String((byte[]) keyObj) : String.valueOf(keyObj);

            if ("total_results".equals(key)) {
                Object countObj = resultList.get(i + 1);
                long count = countObj instanceof Long ? (Long) countObj :
                        (countObj instanceof byte[] ? Long.parseLong(new String((byte[]) countObj)) : 0);
                log.info("RESP3 总匹配数量: {}", count);
            } else if ("results".equals(key)) {
                Object resultsObj = resultList.get(i + 1);
                if (resultsObj instanceof List) {
                    List<Object> results = (List<Object>) resultsObj;
                    log.info("RESP3 结果列表大小: {}", results.size());
                    parseResp3DocumentList(results, documents);
                }
            }
        }
    }

    /**
     * 解析 RESP3 格式的文档列表
     */
    @SuppressWarnings("unchecked")
    private void parseResp3DocumentList(List<Object> results, List<StoredDocument> documents) {
        for (Object docObj : results) {
            if (!(docObj instanceof List)) continue;

            List<Object> docMap = (List<Object>) docObj;
            String docId = null;
            List<Object> extraAttrs = null;

            // 解析文档的 map 结构: [key1, value1, key2, value2, ...]
            for (int i = 0; i < docMap.size() - 1; i += 2) {
                Object keyObj = docMap.get(i);
                String key = keyObj instanceof byte[] ? new String((byte[]) keyObj) : String.valueOf(keyObj);

                if ("id".equals(key)) {
                    Object idObj = docMap.get(i + 1);
                    docId = idObj instanceof byte[] ? new String((byte[]) idObj) : String.valueOf(idObj);
                } else if ("extra_attributes".equals(key)) {
                    Object attrsObj = docMap.get(i + 1);
                    if (attrsObj instanceof List) {
                        extraAttrs = (List<Object>) attrsObj;
                    }
                }
            }

            if (docId != null && extraAttrs != null) {
                StoredDocument doc = parseDocumentFields(docId, extraAttrs);
                if (doc != null) {
                    documents.add(doc);
                }
            }
        }
    }

    /**
     * 解析文档字段
     */
    private StoredDocument parseDocumentFields(String docId, List<Object> fields) {
        StoredDocument doc = new StoredDocument();
        doc.setId(docId);

        // 解析字段（字段名和值交替出现）
        for (int j = 0; j < fields.size() - 1; j += 2) {
            Object fieldNameObj = fields.get(j);
            Object fieldValueObj = fields.get(j + 1);

            String fieldName = fieldNameObj instanceof byte[]
                    ? new String((byte[]) fieldNameObj)
                    : fieldNameObj.toString();
            String fieldValue = fieldValueObj instanceof byte[]
                    ? new String((byte[]) fieldValueObj)
                    : fieldValueObj.toString();

            switch (fieldName) {
                case "content":
                    doc.setContent(fieldValue);
                    break;
                case "source":
                    doc.setSource(fieldValue);
                    break;
                case "page":
                    try {
                        doc.setChunkIndex(Integer.parseInt(fieldValue));
                    } catch (NumberFormatException e) {
                        doc.setChunkIndex(0);
                    }
                    break;
            }
        }

        if (doc.getContent() != null && !doc.getContent().isEmpty()) {
            log.info("成功解析文档: id={}, contentLength={}", doc.getId(), doc.getContent().length());
            return doc;
        } else {
            log.warn("文档内容为空，跳过: {}", docId);
            return null;
        }
    }

    /**
     * 将 float 数组转换为字节数组（小端序，与 Redis 向量格式兼容）
     */
    private byte[] floatArrayToBytes(float[] floats) {
        ByteBuffer buffer = ByteBuffer.allocate(floats.length * 4);
        buffer.order(ByteOrder.LITTLE_ENDIAN);
        for (float f : floats) {
            buffer.putFloat(f);
        }
        return buffer.array();
    }

    /**
     * 使用DashScope Embedding API生成文本向量
     *
     * @param text 文本
     * @return 向量
     */
    private float[] generateEmbedding(String text) throws Exception {
        // 构建请求（OpenAI兼容模式）
        ObjectNode requestBody = objectMapper.createObjectNode();
        requestBody.put("model", dashScopeProperties.getEmbedding().getModel());
        requestBody.put("input", text);

        // 设置请求头
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);
        headers.set("Authorization", "Bearer " + dashScopeProperties.getApiKey());

        HttpEntity<String> request = new HttpEntity<>(
                objectMapper.writeValueAsString(requestBody), headers);

        // 调用Embedding API（OpenAI兼容模式）
        String url = dashScopeProperties.getBaseUrl() + "/embeddings";
        log.debug("调用Embedding API: {}", url);
        ResponseEntity<String> response = restTemplate.postForEntity(url, request, String.class);

        // 解析响应（OpenAI兼容模式）
        JsonNode responseJson = objectMapper.readTree(response.getBody());
        JsonNode embeddingNode = responseJson
                .path("data")
                .path(0)
                .path("embedding");

        if (embeddingNode.isArray()) {
            ArrayNode arrayNode = (ArrayNode) embeddingNode;
            float[] embedding = new float[arrayNode.size()];
            for (int i = 0; i < arrayNode.size(); i++) {
                embedding[i] = (float) arrayNode.get(i).asDouble();
            }
            return embedding;
        }

        throw new Exception("无法生成文本向量");
    }

    /**
     * 清空向量库
     * 删除所有文档并重建索引
     */
    public void clear() {
        try {
            RedisCommands<byte[], byte[]> commands = lettuceConnection.sync();

            // 1. 删除索引
            try {
                CommandArgs<byte[], byte[]> dropArgs = new CommandArgs<>(ByteArrayCodec.INSTANCE)
                        .add(INDEX_NAME.getBytes(StandardCharsets.UTF_8));
                commands.dispatch(RediSearchCommand.FT_DROPINDEX, new ArrayOutput<>(ByteArrayCodec.INSTANCE), dropArgs);
                log.info("已删除索引: {}", INDEX_NAME);
            } catch (Exception e) {
                log.warn("删除索引失败（可能不存在）: {}", e.getMessage());
            }

            // 2. 删除所有文档
            List<byte[]> keys = commands.keys((DOC_PREFIX + "*").getBytes(StandardCharsets.UTF_8));
            if (keys != null && !keys.isEmpty()) {
                commands.del(keys.toArray(new byte[0][]));
                log.info("已删除 {} 个文档", keys.size());
            }

            // 3. 重建索引
            createIndexIfNotExists();

            log.info("向量库已完全重置");
        } catch (Exception e) {
            log.error("清空向量库失败: {}", e.getMessage());
        }
    }

    /**
     * 获取向量库大小
     * 使用 Lettuce 原生命令统计文档数量
     */
    public int size() {
        try {
            RedisCommands<byte[], byte[]> commands = lettuceConnection.sync();
            List<byte[]> keys = commands.keys((DOC_PREFIX + "*").getBytes(StandardCharsets.UTF_8));
            int count = keys != null ? keys.size() : 0;
            log.debug("向量库大小: {}", count);
            return count;
        } catch (Exception e) {
            log.warn("获取向量库大小失败: {}", e.getMessage());
        }
        return 0;
    }

    /**
     * RediSearch 自定义命令
     */
    private enum RediSearchCommand implements ProtocolKeyword {
        FT_INFO("FT.INFO"),
        FT_CREATE("FT.CREATE"),
        FT_SEARCH("FT.SEARCH"),
        FT_DROPINDEX("FT.DROPINDEX");

        private final byte[] bytes;

        RediSearchCommand(String name) {
            this.bytes = name.getBytes(StandardCharsets.US_ASCII);
        }

        @Override
        public byte[] getBytes() {
            return bytes;
        }
    }

    /**
     * 存储的文档
     */
    public static class StoredDocument {
        private String id;
        private String content;
        private String source;
        private int chunkIndex;
        private float[] embedding;

        public String getId() {
            return id;
        }

        public void setId(String id) {
            this.id = id;
        }

        public String getContent() {
            return content;
        }

        public void setContent(String content) {
            this.content = content;
        }

        public String getSource() {
            return source;
        }

        public void setSource(String source) {
            this.source = source;
        }

        public int getChunkIndex() {
            return chunkIndex;
        }

        public void setChunkIndex(int chunkIndex) {
            this.chunkIndex = chunkIndex;
        }

        public float[] getEmbedding() {
            return embedding;
        }

        public void setEmbedding(float[] embedding) {
            this.embedding = embedding;
        }
    }
}
