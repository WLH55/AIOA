/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.repository;

import com.aiwork.helper.entity.User;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 用户数据访问接口
 * 对应Go版本: internal/model/usermodel.go
 */
@Repository
public interface UserRepository extends MongoRepository<User, String> {

    /**
     * 根据用户名查找用户
     * 对应Go: FindByName
     */
    Optional<User> findByName(String name);

    /**
     * 查找管理员用户
     * 对应Go: FindAdminUser
     */
    Optional<User> findByIsAdminTrue();

    /**
     * 根据用户名列表查找用户
     * 对应Go: List with name filter
     */
    List<User> findByNameIn(List<String> names);

    /**
     * 根据ID列表查找用户
     * 对应Go: List with ids filter
     */
    List<User> findByIdIn(List<String> ids);

    /**
     * 根据状态查找用户
     */
    List<User> findByStatus(Integer status);
}