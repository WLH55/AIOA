/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.repository;

import com.aiwork.helper.entity.Todo;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 待办事项数据访问接口
 * 对应Go版本: internal/model/todomodel.go
 */
@Repository
public interface TodoRepository extends MongoRepository<Todo, String> {

    /**
     * 根据创建人ID查找待办列表
     */
    List<Todo> findByCreatorId(String creatorId);

    /**
     * 根据执行人ID查找待办列表
     * 使用Query注解查询嵌入文档中的userId
     * 对应Go: List with UserId filter (executes.userId)
     */
    @Query("{'executes.userId': ?0}")
    Page<Todo> findByExecuteUserId(String userId, Pageable pageable);

    /**
     * 根据执行人ID和时间范围查找待办
     * 对应Go: List with UserId, StartTime, EndTime filters
     */
    @Query("{'executes.userId': ?0, 'createAt': {$gte: ?1, $lte: ?2}}")
    Page<Todo> findByExecuteUserIdAndTimeRange(String userId, Long startTime, Long endTime, Pageable pageable);

    /**
     * 根据待办状态查找
     */
    List<Todo> findByTodoStatus(Integer status);

    /**
     * 根据创建人ID和状态查找
     */
    List<Todo> findByCreatorIdAndTodoStatus(String creatorId, Integer status);

    /**
     * 统计执行人的待办数量
     */
    @Query(value = "{'executes.userId': ?0}", count = true)
    Long countByExecuteUserId(String userId);
}