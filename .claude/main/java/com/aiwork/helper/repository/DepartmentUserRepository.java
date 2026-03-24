/**
 * @author: 公众号：IT杨秀才
 * @doc:后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 */
package com.aiwork.helper.repository;

import com.aiwork.helper.entity.DepartmentUser;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;

import java.util.List;

/**
 * author:  公众号：IT杨秀才
 * 后端，AI知识进阶，后端面试场景题大全：https://golangstar.cn/
 * 部门用户关联数据访问接口
 * 对应Go版本: internal/model/departmentusermodel.go
 */
@Repository
public interface DepartmentUserRepository extends MongoRepository<DepartmentUser, String> {

    /**
     * 根据部门ID查找所有用户关联
     */
    List<DepartmentUser> findByDepId(String depId);

    /**
     * 根据用户ID查找所有部门关联
     */
    List<DepartmentUser> findByUserId(String userId);

    /**
     * 根据部门ID和用户ID查找关联
     */
    DepartmentUser findByDepIdAndUserId(String depId, String userId);

    /**
     * 根据部门ID删除所有关联
     */
    void deleteByDepId(String depId);

    /**
     * 根据用户ID删除所有关联
     */
    void deleteByUserId(String userId);

    /**
     * 根据部门ID和用户ID删除关联
     */
    void deleteByDepIdAndUserId(String depId, String userId);

    /**
     * 统计部门的用户数量
     */
    Long countByDepId(String depId);

    /**
     * 统计用户所在的部门数量
     */
    Long countByUserId(String userId);
}